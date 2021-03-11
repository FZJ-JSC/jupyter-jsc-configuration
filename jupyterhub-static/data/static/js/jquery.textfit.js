/**
 * jQuery Text Fit v1.0
 * https://github.com/nbrunt/TextFit
 *
 * Copyright 2013 Nick Brunt
 * http://nickbrunt.com
 *
 * Free to use and abuse under the MIT license.
 * http://www.opensource.org/licenses/mit-license.php
 */

(function( $ ) {

  var methods = {

    /**
     *  Width
     *
     *  Returns the width in pixels of the given text, based on
     *  the font size and style of the target element.
     */
    width : function(string) {

      // Create ruler with some default styles and font
      // information from target element
      var ruler = $("<span>" + string + "</span>").css({
        'position'    : 'absolute',
        'white-space' : 'nowrap',
        'visibility'  : 'hidden'
      }).css("font", this.css("font"));

      // Render ruler, measure, then remove
      $("body").append(ruler);
      var w = ruler.width();
      ruler.remove();

      return w;
    },

    /**
     *  BestFit
     *
     *  Adjusts the font size of the target element so that
     *  the string fits it perfectly.
     *
     *  The target element must have an absolute width and height.
     */
    bestfit_button_start_after : function() {
      var fs = parseInt($(".resize-text-button").css("font-size"), 10);
      var min_text = 14;
      var max_text = 64;

      // Wrap the content of the target element in a div with
      // with the same width
      var i = innerWrap(this);

      // Keep reducing the font size of the target element
      // until the inner div fits
      var j = 0;
      while (i.height() < this.height() && ++j < 50) {
        this.css("font-size", ++fs + "px");
      }
      j = 0;
      while (i.height() > this.height() && ++j < 50) {
        this.css("font-size", --fs + "px");
      }
      j = 0;
      while (i.width() > this.width() && ++j < 50) {
        this.css("font-size", --fs + "px");
      }
      if ( fs < min_text ) {
        fs = min_text
      } else if ( fs > max_text ) {
        fs = max_text
      }
      this.css("font-size", fs + "px");
      removeWrap(i);
      return this;
    },
    bestfit_button_start : function() {
      var fs = parseInt(this.css("font-size"), 10);
      var min_text = 14;
      var max_text = 64;

      // Wrap the content of the target element in a div with
      // with the same width
      var i = innerWrap(this);

      // Keep reducing the font size of the target element
      // until the inner div fits
      var j = 0;
      while (i.height() < this.height() && ++j < 50) {
        this.css("font-size", ++fs + "px");
        this.css("line-height", fs + "px");
      }
      j = 0;
      while (i.height() > this.height() && ++j < 50) {
        this.css("font-size", --fs + "px");
        this.css("line-height", fs + "px");
      }
      j = 0;
      while (i.width() > this.width() && ++j < 50) {
        this.css("font-size", --fs + "px");
        this.css("line-height", fs + "px");
      }
      if ( fs < min_text ) {
        fs = min_text
      } else if ( fs > max_text ) {
        fs = max_text
      }
      this.css("font-size", fs + "px");
      this.css("line-height", fs +"px");
      $(".resize-text-button-login").css("font-size", fs + "px");
      $(".resize-text-button-login").css("line-height", fs + "px");
      $(".resize-text-top-button-login").css("font-size", fs + "px");
      $(".resize-text-top-button-register").css("font-size", fs + "px");
      $(".resize-text-top-button-register").css("height", $(".resize-text-top-button-login").css("height"));
      removeWrap(i);
      return this;
    },
    bestfit_button : function() {
      var fs = parseInt(this.css("font-size"), 10);

      // Wrap the content of the target element in a div with
      // with the same width
      var i = innerWrap(this);

      // Keep reducing the font size of the target element
      // until the inner div fits
      var j = 0;
      while (i.height() < this.height() && ++j < 50) {
        this.css("font-size", ++fs + "px");
        this.css("line-height", fs + "px");
      }
      j = 0;
      while (i.height() > this.height() && ++j < 50) {
        this.css("font-size", --fs + "px");
        this.css("line-height", fs + "px");
      }
      while (i.width() > this.width() && ++j < 50) {
        this.css("font-size", --fs + "px");
        this.css("line-height", fs + "px");
      }

      this.css("line-height", fs + "px");
      removeWrap(i);
      return this;
    },
    bestfit_min : function() {
      var fs = parseInt(this.css("font-size"), 10);
      var min = 14;

      // Wrap the content of the target element in a div with
      // with the same width
      var i = innerWrap(this);

      // Keep reducing the font size of the target element
      // until the inner div fits
      var j = 0;
      while (i.height() < this.height() && ++j < 50) {
        this.css("font-size", ++fs + "px");
      }
      j = 0;
      while (i.height() > this.height() && ++j < 50) {
        this.css("font-size", --fs + "px");
      }
      if ( fs < min ){
        this.css("font-size", min + "px");
      }

      removeWrap(i);
      return this;
    },

    bestfit : function() {
      var fs = parseInt(this.css("font-size"), 10);

      // Wrap the content of the target element in a div with
      // with the same width
      var i = innerWrap(this);

      // Keep reducing the font size of the target element
      // until the inner div fits
      var j = 0;
      while (i.height() < this.height() && ++j < 50) {
        this.css("font-size", ++fs + "px");
      }
      j = 0;
      while (i.height() > this.height() && ++j < 50) {
        this.css("font-size", --fs + "px");
      }

      removeWrap(i);
      return this;
    },

    /**
     *  Truncate
     *
     *  Trims the contents of the target element to the size
     *  of the element.
     *
     *  The target element must have an absolute width and height.
     */
    truncate : function(length) {
      var i = innerWrap(this);
      var h;

      while (i.height() > this.height()) {
        h = i.html();
        i.html(h.substring(0, h.length-4));
        i.append("...");
      }

      removeWrap(i);
      return this;
    }

  };


  $.fn.textfit = function( method ) {
    
    //If applied on multiple items
    if (this.length > 1) {
        this.each(function () {
            $(this).textfit(method);
        });
        return;
    }

    // Method calling logic
    if ( methods[method] ) {
      return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
    } else if ( typeof method === 'object' || ! method ) {
      return methods.init.apply( this, arguments );
    } else {
      $.error( 'Method ' +  method + ' does not exist on jQuery.textfit' );
    }

  };


  // Helper methods

  var innerWrap = function( el ) {
    // Wrap the content of the target element in a div with
    // with the same width
    el.wrapInner($("<div id='textfit-inner'></div>")
                 .css("width", el.css("width")));
    return $("#textfit-inner");
  };

  var removeWrap = function( el ) {
    el.replaceWith(el.contents());
  };

})( jQuery );

