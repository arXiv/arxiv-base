/**
  * Implements dismissable notifications.
  *
  * To use, insert an element (e.g. a button) with the class
  * `notification-dismiss` that is the direct child of the element that you
  * want to be dismissable. For example:
  *
  * <div class="notification">
  *   <button class="notification-dismiss">Go away</button>
  *   The parent .notification div will be hidden when the button is clicked.
  * </div>
  *
  */

var dismiss_notification_factory = function(elem) {
    var dismiss_notification = function() {
        elem.parentElement.style.display = 'none';
    }
    return dismiss_notification;
}

window.addEventListener('DOMContentLoaded', function() {
    var elems = document.getElementsByClassName('notification-dismiss');
    for (i = 0; i < elems.length; i++) {
        elems[i].addEventListener('click', dismiss_notification_factory(elems[i]));
    }
});
