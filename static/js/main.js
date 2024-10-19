(function ($) {
  "use strict";

  /*===========================================
        Table of contents
    01. On Load Function
    02. Preloader
    03. Mobile Menu Active
    04. Sticky fix
    05. Scroll To Top
    06. Set Background Image
    07. Popup Sidemenu
    08. Search Box Popup
    09. Magnific Popup
    10. Filter Menu
    11. Indicator
    12. Title Rotate
    13. Slider Tab
    14. Range Slider
    15. Procut Zoom Img
    16. Quantity Adder
    17. Rating Input Class Added
    18. Tab Animation
    19. Button Hove Effect
    00. Right Click Disable
    00. Inspect Element Disable
  =============================================*/

  /*---------- 03. Mobile Menu Active ----------*/
  $('.mobile-menu-active').vsmobilemenu({
    menuContainer: '.vs-mobile-menu',
    expandScreenWidth: $('.mobile-menu-active').data('expand'),
    menuToggleBtn: '.vs-menu-toggle',
  });

  /*---------- 04. Sticky fix ----------*/
  var lastScrollTop = '';
  var scrollToTopBtn = '.scrollToTop'

  function stickyMenu($targetMenu, $toggleClass) {
    var st = $(window).scrollTop();
    if ($(window).scrollTop() > 600) {
      if (st > lastScrollTop) {
        $targetMenu.removeClass($toggleClass);

      } else {
        $targetMenu.addClass($toggleClass);
      };
    } else {
      $targetMenu.removeClass($toggleClass);
    };
    lastScrollTop = st;
  };
  $(window).on("scroll", function () {
    stickyMenu($('.sticky-header'), "active");
    if ($(this).scrollTop() > 400) {
      $(scrollToTopBtn).addClass('show');
    } else {
      $(scrollToTopBtn).removeClass('show');
    }
  });



  /*---------- 05. Scroll To Top ----------*/
  $(scrollToTopBtn).on('click', function (e) {
    e.preventDefault();
    $('html, body').animate({
      scrollTop: 0
    }, 3000);
    return false;
  });




  /*---------- 06.Set Background Image ----------*/
  if ($('[data-bg-src]').length > 0) {
    $('[data-bg-src]').each(function () {
      var src = $(this).attr('data-bg-src');
      $(this).css({
        'background-image': 'url(' + src + ')'
      });
    });
  };


  /*---------- 07. Popup Sidemenu ----------*/
  function popupSideMenu($sideMenu, $sideMunuOpen, $sideMenuCls, $toggleCls) {
    // Sidebar Popup
    $($sideMunuOpen).on('click', function (e) {
      e.preventDefault();
      $($sideMenu).addClass($toggleCls);
    });
    $($sideMenu).on('click', function (e) {
      e.stopPropagation();
      $($sideMenu).removeClass($toggleCls)
    });
    var sideMenuChild = $sideMenu + ' > div';
    $(sideMenuChild).on('click', function (e) {
      e.stopPropagation();
      $($sideMenu).addClass($toggleCls)
    });
    $($sideMenuCls).on('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      $($sideMenu).removeClass($toggleCls);
    });
  };
  popupSideMenu('.sidemenu-wrapper', '.sideMenuToggler', '.sideMenuCls', 'show');


  /*---------- 08. Search Box Popup ----------*/
  function popupSarchBox($searchBox, $searchOpen, $searchCls, $toggleCls) {
    $($searchOpen).on('click', function (e) {
      e.preventDefault();
      $($searchBox).addClass($toggleCls);
    });
    $($searchBox).on('click', function (e) {
      e.stopPropagation();
      $($searchBox).removeClass($toggleCls);
    });
    $($searchBox).find('form').on('click', function (e) {
      e.stopPropagation();
      $($searchBox).addClass($toggleCls);
    });
    $($searchCls).on('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      $($searchBox).removeClass($toggleCls);
    });
  };
  popupSarchBox('.popup-search-box', '.searchBoxTggler', '.searchClose', 'show');


  /*----------- 11. Indicator ----------*/
  $.fn.indicator = function () {
    var $menu = $(this),
      $linkBtn = $menu.find('a'),
      $btn = $menu.find('button');
    // Append indicator
    $menu.append('<span class="indicator"></span>');
    var $line = $menu.find('.indicator');
    // Check which type button is Available
    if ($linkBtn.length) {
      var $currentBtn = $linkBtn;
    } else if ($btn.length) {
      var $currentBtn = $btn
    }
    // On Click Button Class Remove
    $currentBtn.on('click', function (e) {
      e.preventDefault();
      $(this).addClass('active');
      $(this).siblings('.active').removeClass('active');
      linePos()
    })
    // Indicator Position
    function linePos() {
      var $btnActive = $menu.find('.active'),
        $height = $btnActive.css('height'),
        $width = $btnActive.css('width'),
        $top = $btnActive.position().top + 'px',
        $left = $btnActive.position().left + 'px';
      $line.css({
        top: $top,
        left: $left,
        width: $width,
        height: $height,
      })
    }

    if ($menu.hasClass('vs-slider-tab')) {
      var linkslide = $menu.data('asnavfor');
      $(linkslide).on('afterChange', function (event, slick, currentSlide, nextSlide) {
        setTimeout(linePos, 10)
      });
    }
    linePos()
  }

  // Call On Load
  if ($('.filter-menu-style1').length) {
    $('.filter-menu-style1').indicator();
  }
  if ($('.tab-indicator').length) {
    $('.tab-indicator').indicator();
  }







  /*----------- 12. Title Rotate ----------*/
  if ($('.title-rotate').length) {
    $('.title-rotate').each(function () {
      var $title = $(this);
      var $letter = $title.text().split('');
      $title.html('')
      for (var i = 0; i < $letter.length; i++) {
        $title.prepend('<span class="letter">' + $letter[i] + '</span>')
      }
    })
  }

  /*----------- 15. Procut Zoom Img ----------*/
  if ($('.zoom-thumb').length) {
    $('.zoom-thumb').each(function () {
      $(this).on('click', function () {
        var srcSet = $(this).data('zoom-image');
        $('.zoom-img').attr('src', srcSet);
      })
    })
  }


  /*----------- 16. Quantity Adder ----------*/
  $('.quantity-plus').each(function () {
    $(this).on('click', function () {
      var $qty = $(this).siblings(".qty-input");
      var currentVal = parseInt($qty.val());
      if (!isNaN(currentVal)) {
        $qty.val(currentVal + 1);
      }
    })
  });

  $('.quantity-minus').each(function () {
    $(this).on('click', function () {
      var $qty = $(this).siblings(".qty-input");
      var currentVal = parseInt($qty.val());
      if (!isNaN(currentVal) && currentVal > 1) {
        $qty.val(currentVal - 1);
      }
    });
  })

  /*----------- 17. Rating Input Class Added ----------*/
  if ($('.vs-rating-input').length > 0) {
    $('.vs-rating-input').each(function () {
      $(this).find('span').on('click', function () {
        $('.vs-rating-input span').addClass('active');
        $(this).nextAll('span').removeClass('active');
      });
    });
  };

  /*----------- 18. Tab Animation ----------*/
  $.fn.tabAnimation = function () {
    $(this).on('hide.bs.tab', function (e) {
      var $old_tab = $($(e.target).attr("href"));
      var $new_tab = $($(e.relatedTarget).attr("href"));

      if ($new_tab.index() < $old_tab.index()) {
        $old_tab.css('position', 'relative').css("bottom", "0").show();
        $old_tab.animate({
          "bottom": "-200px"
        }, 300, function () {
          $old_tab.css("bottom", 0).removeAttr("style");
        });
      } else {
        $old_tab.css('position', 'relative').css("top", "0").show();
        $old_tab.animate({
          "top": "-200px"
        }, 300, function () {
          $old_tab.css("top", 0).removeAttr("style");
        });
      }
    });
    $(this).on('show.bs.tab', function (e) {
      var $new_tab = $($(e.target).attr("href"));
      var $old_tab = $($(e.relatedTarget).attr("href"));

      if ($new_tab.index() > $old_tab.index()) {
        $new_tab.css('position', 'relative').css("bottom", "-200px");
        $new_tab.animate({
          "bottom": "0"
        }, 500);
      } else {
        $new_tab.css('position', 'relative').css("top", "-200px");
        $new_tab.animate({
          "top": "0"
        }, 500);
      }
    });
  }

  $('a[data-bs-toggle="tab"]').tabAnimation();



  /*----------- 19. Button Hove Effect ----------*/
  $.fn.hoverClass = function (element, eleClass) {
    $(this).each(function () {
      $(this).on('mouseenter', function () {
        $(element).addClass(eleClass);
      }).on('mouseleave', function () {
        $(element).removeClass(eleClass);
      })
    })
  };

  $('.vs-btn:not(.style3), .ls-arrow, .slick-arrow').hoverClass('.vs-cursor, .vs-cursor2', 'style2');


  /*----------- 21. Counter Split ----------*/
  $('.counter-number').each(function () {
    var counter = $(this);
    var text = counter.html().split('');
    counter.html('');
    for (var i = 0; i < text.length; i++) {
      var digit = '<span class="digit">' + text[i] + '</span>'
      counter.append(digit)
    }
  })

  /*---------- 06.Set Background Image ----------*/
  if ($("[data-bg-src]").length > 0) {
    $("[data-bg-src]").each(function () {
      var src = $(this).attr("data-bg-src");
      $(this).css("background-image", "url(" + src + ")");
      $(this).removeAttr("data-bg-src").addClass("background-image");
    });
  }


})(jQuery);