#How to use this implementation of Font Awesome

This is a minimal svg implementation of font-awesome. Will also work with other svg libraries or custom code.
We display the svg inline.

## Add new icons to this implementation
To add a new font-awesome icon just grab the source code for the icon you need from here and paste it into your page:
https://github.com/FortAwesome/Font-Awesome/tree/master/svgs/

(Optional) We can also self-host the svg files for future use as an img, background image, etc. Upload svgs here:
https://github.com/arXiv/arxiv-base/tree/develop/arxiv/base/static/fontawesome-svgs/svgs

## Add an icon to your page
Add icons using inline svg. Apply the "icon" class and a color class to the svg tag. Ex:
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-white"><path d="M502.3 190.8c3.9-3.1 9.7-.2 9.7 4.7V400c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V195.6c0-5 5.7-7.8 9.7-4.7 22.4 17.4 52.1 39.5 154.1 113.6 21.1 15.4 56.7 47.8 92.2 47.6 35.7.3 72-32.8 92.3-47.6 102-74.1 131.6-96.3 154-113.7zM256 320c23.2.4 56.6-29.2 73.4-41.4 132.7-96.3 142.8-104.7 173.4-128.7 5.8-4.5 9.2-11.5 9.2-18.9v-19c0-26.5-21.5-48-48-48H48C21.5 64 0 85.5 0 112v19c0 7.4 3.4 14.3 9.2 18.9 30.6 23.9 40.7 32.4 173.4 128.7 16.8 12.2 50.2 41.8 73.4 41.4z"/></svg>

The following color classes are available:
.filter-white
.filter-black
.filter-grey
.filter-blue
.filter-red
All non-white icons have a white hover color. White icons have a grey hover color. Add more color and hover classes as needed to the custom sass file.

The icon will scale based on the font size of it's container so you shouldn't need to adjust height or width manually with css (though you can if you need to).

## Making icons accessible
SVG has excellent cross browser and device support, fallbacks are no longer needed. To also make sure icons are accessible to screen readers do the following:

- If an icon is purely decorative add role="presentation" to the svg tag so screen readers know to skip it. No further action is needed.
- If it is a functional icon and should be understood by screen readers add title and desc tags inside the svg, and role and aria-labelledby attributes to the svg tag. Write clear and concise title and desc tags for screen readers. Ex:

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-white" role="img" aria-labelledby="icon-title-contact icon-desc-contact"><title id="icon-title-contact">contact arXiv</title><desc id="icon-desc-contact">Click here to email us</desc><path d="M502.3 190.8c3.9-3.1 9.7-.2 9.7 4.7V400c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V195.6c0-5 5.7-7.8 9.7-4.7 22.4 17.4 52.1 39.5 154.1 113.6 21.1 15.4 56.7 47.8 92.2 47.6 35.7.3 72-32.8 92.3-47.6 102-74.1 131.6-96.3 154-113.7zM256 320c23.2.4 56.6-29.2 73.4-41.4 132.7-96.3 142.8-104.7 173.4-128.7 5.8-4.5 9.2-11.5 9.2-18.9v-19c0-26.5-21.5-48-48-48H48C21.5 64 0 85.5 0 112v19c0 7.4 3.4 14.3 9.2 18.9 30.6 23.9 40.7 32.4 173.4 128.7 16.8 12.2 50.2 41.8 73.4 41.4z"/></svg>
