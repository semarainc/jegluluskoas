(function ($) {
 "use strict";
    /*---------------------
       Circular Bars - Knob
    --------------------- */	
	  if(typeof($.fn.knob) != 'undefined') {
		$('.knob').each(function () {
		  var $this = $(this),
			  knobVal = $this.attr('data-rel');
	
		  $this.knob({
			'draw' : function () { 
			  $(this.i).val(this.cv )//percent was here before
			}
		  });
		  
		 
		});
    }	

})(jQuery);
