# arXiv Email Templates

This set of templates is based heavily on Lee Munroe's [Really Simple Free
Responsive Email Template] (https://github.com/leemunroe/responsive-html-email-template)
with additional enhancements from Ted Goas's [Cerberus](https://tedgoas.github.io/Cerberus/).
We are using templates with pre-coded inline styling to prevent the need for a
separate tool to do the inlining. The original Munroe template was inlined, the
rest is intended to be style-edited by hand. Our emails are not all that
complicated from a design and layout perspective.

## Jinja Template Regions

Block name | Template file | Notes
---------- | ------------- | -----
email_title | head.html | Displays on some mobile devices
preheader | base.html | Displays in some clients as email preview
message_title_wrapper | base.html | see Formatting and Inline Styles
message_title | base.html | content replacement only
message_body | base.html | requires formatting and inline styles
signature | base.html | OK to send with default
addl_footer | footer-table.html | OK to send with default

## Formatting and Inline Styles

Due to the nature of HTML email, it's not entirely possible to separate content
entirely from styling the way we usually do.

### Message title

If the default style of the title needs to be changed for some reason, the
desired HTML element and styles can be specified using the
message_title_wrapper block. Most of the time this can (and should) be left alone.

```
  <h1 style="font-size: 16px; font-weight: bold; margin: 0; margin-bottom: 15px;">{% block message_title %}A message from arXiv {% endblock %}</h1>
```

### Message body

Every paragraph of the body should be wrapped in a paragraph tag with inline
margin styling. Links and bold text should follow the example format.
In general, styling support in email needs to include old-school fallbacks
(thanks, Outlook).

```
  <p style="margin: 0; margin-bottom: 15px;">This is a <b>test message</b><br />
  If you are seeing this in the wild, <a href="mailto:support@arxiv.org" style="color: #0068ac; text-decoration: underline;"><font color="#0068ac">let us know</font></a>.</p>
```

## HTML Email - Coding Circa 1999

- All styles should be explicitly defined and inline.
- Some CSS in the <head> is included for email clients that can use it.
- All layout needs to be done with tables.
- HTML4 only.
- Keep markup as simple as possible.
- When in doubt, consult a reliable reference.
- Test, test, test on every platform possible. Use [Putsmail](https://putsmail.com/).
- Include a plaintext version with every email.

## References

- https://tedgoas.github.io/Cerberus/
- https://github.com/leemunroe/responsive-html-email-template
- https://www.smashingmagazine.com/2017/01/introduction-building-sending-html-email-for-web-developers/
- https://webdesign.tutsplus.com/articles/build-an-html-email-template-from-scratch--webdesign-12770
