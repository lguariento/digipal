$(document).ready(function() {

	var tabs = $('a[data-toggle="tab"]');
	tabs.on('shown.bs.tab', function(e) {
		var dialog = $('.dialog_annotations');
		var dialog_settings = $('#modal_settings');
		var dialog_filters = $('#allographs_filtersBox');

		if (e.target.getAttribute('data-target') != '#annotator') {

			if (window.history && window.history.pushState) {
				history.pushState(null, null, $(this).attr('href'));
			} else {
				window.location.href = $(this).attr('href');
			}

			if (dialog.length) {
				dialog.parent().fadeOut();
			}

			if (dialog_settings.hasClass('ui-dialog-content') && dialog_settings.dialog('isOpen')) {
				dialog_settings.parent().fadeOut();
			}

			if (dialog_filters.hasClass('ui-dialog-content') && dialog_filters.dialog('isOpen')) {
				dialog_filters.parent().fadeOut();
			}

			if (e.target.getAttribute('data-target') == '#allographs') {
				if (annotator.has_changed) {
					allographsPage.refresh();
					//annotator.refresh_layer();
				}
			}
		} else {
			if (typeof annotator == 'undefined') {
				main(true);
			}

			loader.toolbar_position();

			if (dialog.length) {
				dialog.parent().fadeIn();
			}

			if (dialog_settings.hasClass('ui-dialog-content') && dialog_settings.dialog('isOpen')) {
				dialog_settings.parent().fadeIn();
			}

			if (dialog_filters.hasClass('ui-dialog-content') && dialog_filters.dialog('isOpen')) {
				dialog_filters.parent().fadeIn();
			}

			history.pushState(null, null, annotator.absolute_image_url);

		}

		return false;
	});

});