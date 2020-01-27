#How to use this implementation of Font Awesome

This is a minimal svg implementation of font-awesome. Will also work with other svg libraries or custom code.
We display the svg inline.

## Add new icons to this implementation
To add a new font-awesome icon just grab the source code for the icon you need from here and paste it into your page:
https://github.com/FortAwesome/Font-Awesome/tree/master/svgs/

(Optional) We can also self-host the svg files for future use as an img, background image, etc. Upload svgs here:
https://github.com/arXiv/arxiv-base/tree/develop/arxiv/base/static/fontawesome-svgs/svgs

## Add an icon to your page
Add icons using inline svg. Apply the "icon" class and a color class to the svg tag. A title tag inside the svg will render as a tooltip in many browsers. Ex:
```
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-blue"><title>tooltip text here</title><path d="M502.3 190.8c3.9-3.1 9.7-.2 9.7 4.7V400c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V195.6c0-5 5.7-7.8 9.7-4.7 22.4 17.4 52.1 39.5 154.1 113.6 21.1 15.4 56.7 47.8 92.2 47.6 35.7.3 72-32.8 92.3-47.6 102-74.1 131.6-96.3 154-113.7zM256 320c23.2.4 56.6-29.2 73.4-41.4 132.7-96.3 142.8-104.7 173.4-128.7 5.8-4.5 9.2-11.5 9.2-18.9v-19c0-26.5-21.5-48-48-48H48C21.5 64 0 85.5 0 112v19c0 7.4 3.4 14.3 9.2 18.9 30.6 23.9 40.7 32.4 173.4 128.7 16.8 12.2 50.2 41.8 73.4 41.4z"/></svg>
```
The icon size will scale based on the font size of it's container so you shouldn't need to adjust height or width manually with css (though you can if you need to).

## Icon color options
The following color classes are available:
.filter-white
.filter-black
.filter-grey
.filter-dark_grey
.filter-blue
.filter-dark_blue
.filter-light_red
.filter-red
.filter-dark_red
.filter-orange
.filter-dark_orange
.filter-yellow
.filter-dark_yellow
.filter-green
.filter-dark_green

a11y color contrast: the regular colors (with the exception of red) have a color contrast of 3.0 or higher, while the dark versions have a color contrast of 4.5 or higher (with white or the light version of each color used in message divs). Red's light color has a contrast of 3.0 or higher, while both the regular and dark versions have a contrast of 4.5 or higher. Red is the only color with a light version.

Hover colors: All non-grey icons have a grey hover color. Grey icons have a black hover color. Add more color and hover classes as needed to the custom sass file.

## Making icons accessible
SVG has excellent cross browser and device support and fallbacks are no longer needed. To also make sure icons are accessible to screen readers do the following:

- If an icon is purely decorative add role="presentation" to the svg tag so screen readers know to skip it. No further action is needed.
- If the icon provides meaning to screen readers add title and/or desc tags inside the svg, and role and aria-labelledby attributes to the svg tag. Write clear and concise title and desc tags for screen readers. Ex:
```
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-green" role="img" aria-labelledby="icon-title-contact icon-desc-contact"><title id="icon-title-contact">Status</title><desc id="icon-desc-contact">approved</desc><path d="M502.3 190.8c3.9-3.1 9.7-.2 9.7 4.7V400c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V195.6c0-5 5.7-7.8 9.7-4.7 22.4 17.4 52.1 39.5 154.1 113.6 21.1 15.4 56.7 47.8 92.2 47.6 35.7.3 72-32.8 92.3-47.6 102-74.1 131.6-96.3 154-113.7zM256 320c23.2.4 56.6-29.2 73.4-41.4 132.7-96.3 142.8-104.7 173.4-128.7 5.8-4.5 9.2-11.5 9.2-18.9v-19c0-26.5-21.5-48-48-48H48C21.5 64 0 85.5 0 112v19c0 7.4 3.4 14.3 9.2 18.9 30.6 23.9 40.7 32.4 173.4 128.7 16.8 12.2 50.2 41.8 73.4 41.4z"/></svg>
```
- If the icon is inside a link add role="presentation" to the svg and an accompanying span tag with a text description. The text can be made only visible to screen readers by adding the Bulma class "is-sr-only". In a series of similar links make sure your screen reader-friendly text is unique. For instance you cannot have multiple links with the identical meaning of "delete", but also need to specify what the link will delete. Ex:
```
<a class="button" href="#">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-blue" role="presentation"><title>Unsubmit</title><path d="M255.545 8c-66.269.119-126.438 26.233-170.86 68.685L48.971 40.971C33.851 25.851 8 36.559 8 57.941V192c0 13.255 10.745 24 24 24h134.059c21.382 0 32.09-25.851 16.971-40.971l-41.75-41.75c30.864-28.899 70.801-44.907 113.23-45.273 92.398-.798 170.283 73.977 169.484 169.442C423.236 348.009 349.816 424 256 424c-41.127 0-79.997-14.678-110.63-41.556-4.743-4.161-11.906-3.908-16.368.553L89.34 422.659c-4.872 4.872-4.631 12.815.482 17.433C133.798 479.813 192.074 504 256 504c136.966 0 247.999-111.033 248-247.998C504.001 119.193 392.354 7.755 255.545 8z"/></svg>
  <span class="is-sr-only">Unsubmit submission id {{ submission.submission_id }}</span>
</a>
```

## Applying a styled bubble popup to an icon
To make an icon display a styled "bubble" tooltip follow this example

```
<a class="icon has-text-link help-bubble" href="#">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon filter-blue" role="presentation"><path d="M256 8C119.043 8 8 119.083 8 256c0 136.997 111.043 248 248 248s248-111.003 248-248C504 119.083 392.957 8 256 8zm0 110c23.196 0 42 18.804 42 42s-18.804 42-42 42-42-18.804-42-42 18.804-42 42-42zm56 254c0 6.627-5.373 12-12 12h-88c-6.627 0-12-5.373-12-12v-24c0-6.627 5.373-12 12-12h12v-64h-12c-6.627 0-12-5.373-12-12v-24c0-6.627 5.373-12 12-12h64c6.627 0 12 5.373 12 12v100h12c6.627 0 12 5.373 12 12v24z"/></svg>
  <span class="sr-only">Click to learn more about Ancillary files</span>
  <div class="bubble-text">Ancillary files will be placed in an /anc directory automatically. Click to learn more.</div>
</a>
```
