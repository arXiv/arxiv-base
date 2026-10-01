# Classify a plan (terraform show -json tfplan | jq -r -f plan_kind.jq):
#   none   nothing to apply
#   image  only the image of existing jobs changes (CI applies without approval)
#   infra  anything else (CI waits for approval in prod)
# Attributes that become unknown in `after` (etag, update_time, ...) are
# computed by the API and ignored; a nested unknown makes before != after,
# so it counts as infra (the safe side).
def strip($u): delpaths($u | map([.])) | del(.template[0].template[0].containers[0].image);

[.resource_changes[]? | select(.change.actions != ["no-op"])] as $c
| if ($c | length) == 0 then "none"
  elif all($c[];
      .type == "google_cloud_run_v2_job" and .change.actions == ["update"]
      and ([.change.after_unknown | to_entries[] | select(.value == true) | .key] as $u
           | (.change.before | strip($u)) == (.change.after | strip($u))))
  then "image"
  else "infra"
  end
