# arXiv Email Templates

This set of templates is based heavily on Lee Munroe's [Really Simple Free
Responsive Email Template] (https://github.com/leemunroe/responsive-html-email-template)
with additional enhancements from Ted Goas's [Cerberus](https://tedgoas.github.io/Cerberus/).
We are using templates with pre-coded inline styling to prevent the need for a
separate tool to do the inlining. The original Munroe template was inlined, the
rest is intended to be style-edited by hand. Our emails are not all that
complicated from a design and layout perspective.

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
