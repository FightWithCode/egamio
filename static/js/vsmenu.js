(function (e) {
    e.fn.vsmobilemenu = function (n) {
        var s = e.extend(
            {
                menuContainer: ".vs-mobile-menu",
                menuToggleClass: "vs-menu-visible",
                expandScreenWidth: 992,
                containerClass: "vs-menu-container",
                meanExpandClass: "vs-mean-expand",
                subMenuParent: "vs-item-has-children",
                subMenuParentToggle: "vs-active",
                subMenuClass: "vs-submenu",
                subMenuToggleClass: "vs-open",
                toggleSpeed: 400,
                menuBody: ".vs-menu-wrapper",
                bodyToggleClass: "vs-body-visible",
                menuToggleBtn: ".vs-menu-toggle",
                btnToggleClass: "vs-active",
            },
            n
        );
        return this.each(function () {
            function n(n) {
                var l = e(n).next("ul").find("ul");
                l.hasClass(s.subMenuToggleClass) && (l.removeClass(s.subMenuToggleClass), l.slideUp(s.toggleSpeed), l.parent().removeClass(s.subMenuParentToggle));
            }
            function l(l) {
                e(l).next("ul").length > 0
                    ? (e(l).parent().toggleClass(s.subMenuParentToggle), e(l).next("ul").slideToggle(s.toggleSpeed), e(l).next("ul").toggleClass(s.subMenuToggleClass), n(l))
                    : e(l).prev("ul").length > 0 && (e(l).parent().toggleClass(s.subMenuParentToggle), e(l).prev("ul").slideToggle(s.toggleSpeed), e(l).prev("ul").toggleClass(s.subMenuToggleClass), n(l));
            }
            function a() {
                var n = "." + s.subMenuClass;
                e(n).each(function () {
                    e(this).hasClass(s.subMenuToggleClass) && (e(this).removeClass(s.subMenuToggleClass), e(this).css("display", "none"), e(this).parent().removeClass(s.subMenuParentToggle));
                });
            }
            function o() {
                i < s.expandScreenWidth
                    ? (g.css("display", "none"), e(s.menuContainer).css("display", ""), e(s.menuBody).css("display", ""))
                    : (g.css("display", ""), e(s.menuContainer).css("display", "none"), e(s.menuBody).css("display", "none"));
            }
            var t = e(this).html();
            e(s.menuContainer).each(function () {
                e(this).on("click", function (e) {
                    e.stopPropagation();
                }),
                    e(this).html(t),
                    e(this)
                        .find("li")
                        .each(function () {
                            var n = e(this).find("ul");
                            n.addClass(s.subMenuClass), n.css("display", "none"), n.parent().addClass(s.subMenuParent), n.prev("a").addClass(s.meanExpandClass), n.next("a").addClass(s.meanExpandClass);
                        });
            });
            var u = "." + s.meanExpandClass;
            e(u).each(function () {
                e(this).on("click", function (e) {
                    e.preventDefault(), l(this);
                });
            }),
                e(s.menuToggleBtn).each(function () {
                    e(this).on("click", function (n) {
                        n.preventDefault(),
                            e(s.menuToggleBtn).toggleClass(s.btnToggleClass),
                            e(s.menuBody).length > 0 && e(s.menuBody).toggleClass(s.bodyToggleClass),
                            e(s.menuContainer).length > 0 && e(s.menuContainer).toggleClass(s.menuToggleClass),
                            a();
                    });
                }),
                e(s.menuBody).length > 0 &&
                    e(s.menuBody).on("click", function (n) {
                        n.stopPropagation(), e(s.menuBody).hasClass(s.bodyToggleClass) && (e(s.menuBody).removeClass(s.bodyToggleClass), e(s.menuContainer).removeClass(s.menuToggleClass), e(s.menuToggleBtn).removeClass(s.btnToggleClass));
                    }),
                e(s.menuBody)
                    .find("div")
                    .on("click", function (e) {
                        e.stopPropagation();
                    });
            var g = e(this);
            let i = e(window).width();
            o(),
                e(window).on("resize", function () {
                    (i = e(window).width()), o();
                });
        });
    };
})(jQuery);
