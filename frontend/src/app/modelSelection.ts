type Profile = { profile_key: string; enabled: boolean };

/** A missing saved selection must never silently redirect writes to another model. */
export function resolveModelSelection(profiles: Profile[], selected: string): string {
  const enabled = profiles.filter(profile => profile.enabled);
  if (selected) return enabled.some(profile => profile.profile_key === selected) ? selected : "";
  return enabled.length === 1 ? enabled[0].profile_key : "";
}
