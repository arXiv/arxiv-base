// File: member_acknowledgement.js

(function() {
  getMemberInstitutionName();
  async function getMemberInstitutionName() {
    label = localStorage.getItem("member_label");
    expires = localStorage.getItem("member_expires");

    expired = true;
    if (expires) {
      expires = new Date(expires);
      now = new Date();
      if (now < expires) {
        expired = false;
      }
    }

    if (expired) {
      localStorage.removeItem("member_label");
      localStorage.removeItem("member_expires");

      lookup_failed = false
      label = localStorage.getItem("member_label");
      if (! label) {
        let result = await fetch("/institutional_banner");
        if (result && result.ok) {
            let j = await result.json();
            label = j["label"];
            if (label) {
              localStorage.setItem("member_label", label);
            }
        } else {
          lookup_failed = true
        }
      }

      expires_ms = 30*24*60*60*1000;
      if (lookup_failed) {
        expires_ms = 1*60*60*1000; // try sooner if db issue.
      }
      const new_expires = new Date();
      new_expires.setTime(new_expires.getTime() + expires_ms);
      localStorage.setItem("member_expires", new_expires);
    }

    if (label) {
      s = 'We gratefully acknowledge support from<br/>';
      s += 'the Simons Foundation and ' + label + ".";
      support_elem = document.getElementById('support-ack-url');
      if (support_elem) {
        support_elem.innerHTML = s;
      }
    }
  }
})();
