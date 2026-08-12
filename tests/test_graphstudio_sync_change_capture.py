from src.graphstudio_sync.change_capture import (
    _identifier,
    iter_oracle_flashback_changes,
    iter_sqlserver_cdc,
    iter_sqlserver_change_tracking,
    iter_watermark_changes,
)


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executions = []
        self.closed = False

    def execute(self, sql, parameters):
        self.executions.append((sql, parameters))

    def fetchmany(self, size):
        result, self.rows = self.rows[:size], self.rows[size:]
        return result

    def close(self):
        self.closed = True


class SqlServerConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)

    def cursor(self, as_dict=False):
        assert as_dict
        return self.cursor_instance


class OracleConnection:
    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)

    def cursor(self):
        return self.cursor_instance


def test_identifiers_reject_injected_policy_columns() -> None:
    assert _identifier("LastUpdatedDate", "camstar_sqlserver") == "[LastUpdatedDate]"
    try:
        _identifier("LastUpdatedDate]; DROP TABLE X;--", "camstar_sqlserver")
    except ValueError as exc:
        assert "Unsafe source identifier" in str(exc)
    else:
        raise AssertionError("Unsafe identifier was accepted")


def test_change_tracking_reader_emits_upsert_and_tombstone() -> None:
    connection = SqlServerConnection(
        [
            {
                "__change_version": 101,
                "__change_operation": "U",
                "HistoryId": "H1",
                "Name": "Updated",
            },
            {
                "__change_version": 102,
                "__change_operation": "D",
                "HistoryId": "H2",
                "Name": None,
            },
        ]
    )

    records = list(
        iter_sqlserver_change_tracking(
            connection,
            schema="CamstarPRD_SCHEMA",
            table="HistoryMainline",
            columns=["HistoryId", "Name"],
            primary_keys=["HistoryId"],
            lower_version=100,
            upper_version=110,
            fetch_size=10,
        )
    )

    assert [record.operation for record in records] == ["update", "delete"]
    assert records[0].row["Name"] == "Updated"
    assert records[1].row is None
    assert records[1].key == {"HistoryId": "H2"}
    sql, parameters = connection.cursor_instance.executions[0]
    assert "CHANGETABLE(CHANGES [CamstarPRD_SCHEMA].[HistoryMainline], %s)" in sql
    assert "TOP (10)" in sql
    assert parameters == (100, 110)
    assert connection.cursor_instance.closed


def test_cdc_reader_keeps_lsn_seqval_resume_position() -> None:
    connection = SqlServerConnection(
        [
            {
                "__start_lsn": bytes.fromhex("00000000000000000001"),
                "__seqval": bytes.fromhex("00000000000000000002"),
                "__operation": 2,
                "HistoryId": "H1",
                "Name": "New",
            },
            {
                "__start_lsn": bytes.fromhex("00000000000000000003"),
                "__seqval": bytes.fromhex("00000000000000000004"),
                "__operation": 1,
                "HistoryId": "H2",
                "Name": "Old",
            },
        ]
    )

    records = list(
        iter_sqlserver_cdc(
            connection,
            capture_instance="CamstarPRD_SCHEMA_HistoryMainline",
            columns=["HistoryId", "Name"],
            primary_keys=["HistoryId"],
            lower_lsn="0x00000000000000000000",
            upper_lsn="0x00000000000000000009",
            fetch_size=10,
        )
    )

    assert [record.operation for record in records] == ["insert", "delete"]
    assert records[0].position == {
        "cdcLsn": "0x00000000000000000001",
        "seqval": "0x00000000000000000002",
        "operationCode": 2,
    }
    assert records[1].row is None
    sql, parameters = connection.cursor_instance.executions[0]
    assert "fn_cdc_get_all_changes_CamstarPRD_SCHEMA_HistoryMainline" in sql
    assert isinstance(parameters[0], bytes)


def test_sqlserver_watermark_reader_is_upper_bounded_and_keyset_ready() -> None:
    connection = SqlServerConnection(
        [{"MfgOrderId": "M2", "LastUpdatedDate": "2026-08-13T12:00:00", "Name": "MO-2"}]
    )

    records = list(
        iter_watermark_changes(
            connection,
            kind="camstar_sqlserver",
            schema="CamstarPRD_SCHEMA",
            table="MfgOrder",
            columns=["Name"],
            primary_keys=["MfgOrderId"],
            watermark_column="LastUpdatedDate",
            lower_bound="2026-08-13T11:00:00",
            upper_bound="2026-08-13T13:00:00",
            fetch_size=10,
        )
    )

    assert records[0].operation == "upsert"
    assert records[0].position["primaryKey"] == {"MfgOrderId": "M2"}
    sql, parameters = connection.cursor_instance.executions[0]
    assert "[LastUpdatedDate] <= %s" in sql
    assert "[LastUpdatedDate] > %s" in sql
    assert parameters == ("2026-08-13T13:00:00", "2026-08-13T11:00:00")


def test_oracle_flashback_reader_emits_delete_event() -> None:
    connection = OracleConnection(
        [{"__operation": "D", "__start_scn": 501, "HISTORYID": "H1", "NAME": "Old"}]
    )

    records = list(
        iter_oracle_flashback_changes(
            connection,
            schema="CAMSTAR",
            table="HISTORYMAINLINE",
            columns=["NAME"],
            primary_keys=["HISTORYID"],
            lower_scn=500,
            upper_scn=550,
            fetch_size=10,
        )
    )

    assert records[0].operation == "delete"
    assert records[0].row is None
    assert records[0].position == {"scn": 501, "primaryKey": {"HISTORYID": "H1"}}
    sql, parameters = connection.cursor_instance.executions[0]
    assert 'VERSIONS BETWEEN SCN :lower_scn AND :upper_scn' in sql
    assert "FETCH FIRST 10 ROWS ONLY" in sql
    assert parameters["lower_scn"] == 500
