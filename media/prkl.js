function scrollForDiv(div) {
	divHeight = parseInt($(div).height());
	divOffset = parseInt($(div).offset().top);
	windowHeight = parseInt($(window).height());
	windowScroll = parseInt($(window).scrollTop());
	divEnd = divHeight + divOffset;
	if (divEnd > windowHeight + windowScroll) {
		$('html, body').animate({
			// 25 should cover the next line of #subj_{{ message }}
			scrollTop: windowScroll + divHeight + 25
		}, 500, 'easeOutSine');
	}
}

