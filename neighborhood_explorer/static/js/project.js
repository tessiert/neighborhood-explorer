/* Project specific Javascript goes here. */

// Change active menu tab
$(document).ready(function () {
  $('li.active').removeClass('active');
  $('a[href="' + location.pathname + '"]')
    .closest('li')
    .addClass('active');
});



// Require valid search criteria to enable 'Submit' button for POI search
$(document).ready(function() {
  $('.poi_menu').on('input change', function() {
    if(!$('#point_of_interest').val() || !$('#radius').val() ||
      !$('#sort_method').val()) {
        $('#poi_submit').prop('disabled', true);        
      }
    else {
      $('#poi_submit').prop('disabled', false);
    }
  });
});



function setSelectedIndex(s, valsearch) {
  // Loop through all the items in drop down list (on search.html page)
  for (i = 0; i< s.options.length; i++) {
      if (s.options[i].value == valsearch) {
          // Item is found. Set its property and exit
          s.options[i].selected = true;
          break;
      }
  }
  return;
}