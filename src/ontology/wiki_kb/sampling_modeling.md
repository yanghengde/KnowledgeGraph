Chapter 15: Sampling and Inspection Modeling
Introduction
Sampling Plans define the quality inspection sampling strategy. Sample Tests define how
the actual inspection is performed. Together they form the complete sampling system:
Plan determines how many to sample, Test determines how to inspect them.

In This Chapter
• SamplingPlan (Sampling Strategy)
• SamplingPlanDetail (Lot-size-based Rule)
• SampleTest (Inspection Execution)
• AQL (Acceptable Quality Level)

SamplingPlan
The strategy layer — defines sampling rate, AQL level, inspection level, switching rules,
and associations to Specs, Resources, and Vendors.

SampleTest
The execution layer — defines the actual inspection procedure: sample type, operator
instructions, data points to collect, defect classification, failure handling, and
reject/scrap reason tracking.

Relationship chain:

    SamplingPlan ──(USES_SAMPLE_TEST)──▶ SampleTest ──(COLLECTS_DATA)──▶ DataCollectionDef
                 ──(HAS_SAMPLING_DETAIL)──▶ SamplingPlanDetail ──▶ AQL
    Spec ──(REQUIRES_SAMPLING)──▶ SamplingPlan

SampleTest Field Definitions:
- Name (String, Required): Unique test name.
- Revision (String, Required): Revision version.
- SampleType (Integer, Required): Test type (variable/attribute).
- Instructions (String): Operator instructions for performing the test.
- Classification (Navigation): Defect classification.
- SubClassification (Navigation): Defect sub-classification.
- AQLRejectReasons (Navigation): AQL reject reason codes.
- DefaultFailureMode (Navigation): Default failure mode for test failures.
- DefaultPEDescription (String): Default production event description.
- AllowMoveOnFailure (Boolean): Allow container move on test failure.
- ScrapCountedRejectsByReason (Boolean): Track scrap rejects by reason.
- DecreaseByRejectCountReason (Navigation): Reason for decrease by reject count.
- DecreaseBySampleSizeReason (Navigation): Reason for decrease by sample size.
- SampleDataPoints (SubentityList): Data points collected during this test.

SamplingPlan Cross-Module Relationships:
- USES_DEFAULT_SAMPLING (to SamplingPlan, MANY_TO_ONE): 由 Product 或 ProductFamily 发起，定义产品主数据上配置的默认质量抽样策略。

