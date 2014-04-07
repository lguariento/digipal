/**
 * Add elements to Lightbox function, updates the collection counter in the main menu
   -- Digipal Project --> digipal.eu
 */

function length_basket_elements(elements) {
	var n = 0;
	if (elements) {
		$.each(elements, function() {
			n += this.length;
		});
	}
	return n;
}

function update_collection_counter() {

	var collections;
	if (localStorage.getItem('collections')) {
		collections = localStorage.getItem('collections');
	} else {
		return false;
	}

	var basket_elements = JSON.parse(collections);
	var menu_links = $('.navLink');
	var basket_element;

	for (var ind = 0; ind < menu_links.length; ind++) {
		if ($.trim(menu_links[ind].innerHTML) == 'Collection') {
			basket_element = $(menu_links[ind]);
			basket_element.attr('id', 'collection_link');
		}
	}

	if (!basket_element) {
		basket_element = $('#collection_link');
	}

	var i = 0;
	for (var d in basket_elements) {
		i++;
	}

	basket_element.html("Collections (" + i + " <i class='fa fa-picture-o'> </i> )");

}

function add_to_lightbox(button, type, annotations, multiple) {
	var selectedCollection = localStorage.getItem('selectedCollection');
	var collections = JSON.parse(localStorage.getItem('collections'));
	var collection_name;
	var collection_id;
	$.each(collections, function(index, value) {
		if (value.id == selectedCollection) {
			current_basket = value;
			collection_name = index;
			collection_id = value.id;
		}
	});

	if (annotations === null) {
		notify('Error. Try again', 'danger');
		return false;
	}

	var flag, i, j, elements, image_id;
	if (multiple) {
		if (current_basket && current_basket.annotations) {
			for (i = 0; i < annotations.length; i++) {
				flag = true;
				for (j = 0; j < current_basket.annotations.length; j++) {
					//console.log(current_basket.annotations[j].graph + " == " + annotations[i].graph)
					if (!annotations[i]) {
						notify('Annotation has not been saved yet. Otherwise, refresh the layer', 'danger');
						return false;
					}
					if (current_basket.annotations[j] == annotations[i]) {
						flag = false;
					}
				}
				if (flag) {
					current_basket.annotations.push(parseInt(annotations[i], 10));
					notify('Image succesfully added to collection', 'success');
				} else {
					notify('Annotation has already been added to Collection', 'danger');
					continue;
				}
			}

		} else {
			current_basket = {};
			current_basket.annotations = [];
			for (i = 0; i < annotations.length; i++) {
				current_basket.annotations.push(parseInt(annotations[i], 10));
			}
		}
		localStorage.setItem('collections', JSON.stringify(collections));
	} else {
		var graph;
		if (type == 'annotation') {
			graph = annotations;
			if (typeof graph == 'undefined' || !graph) {
				notify('Annotation has not been saved yet', 'danger');
				return false;
			}
			if (current_basket.annotations === undefined) {
				current_basket.annotations = [];
			}
			elements = current_basket.annotations;
		} else {
			graph = annotations;
			if (current_basket.images === undefined) {
				current_basket.images = [];
			}
			elements = current_basket.images;
		}

		if (current_basket && elements && elements.length) {
			for (j = 0; j < elements.length; j++) {
				flag = true;

				if (type == 'annotation') {
					var el;

					if (elements[j] == graph) {
						flag = false;
						break;
					}

				} else {
					if (elements[j].id == graph) {
						flag = false;
						break;
					}
				}
			}
			if (flag) {
				if (type == 'annotation') {
					if (annotations == 'undefined' || !annotations) {
						notify('Annotation has not been saved yet', 'danger');
						return false;
					}
					elements.push(annotations);
					notify('Annotation succesfully added to collection', 'success');
				} else {
					if (typeof annotator != 'undefined') {
						image_id = annotator.image_id;
					} else {
						image_id = graph;
					}
					elements.push(image_id);
					notify('Image succesfully added to collection', 'success');
				}
			} else {
				if (type == 'annotation') {
					notify('Annotation has already been added to Collection', 'danger');
				} else {
					notify('Page has already been added to Collection', 'danger');
				}
				return false;
			}

			localStorage.setItem('collections', JSON.stringify(collections));

		} else {

			if (type == 'annotation') {
				if (current_basket.hasOwnProperty('images')) {
					current_basket.annotations = [];
					current_basket.annotations.push(annotations);
				} else {
					current_basket = {};
					current_basket.annotations = [];
					current_basket.annotations.push(annotations);
					current_basket['id'] = collection_id;
					collections[collection_name] = current_basket;
				}

			} else {

				if (typeof annotator != 'undefined') {
					image_id = annotator.image_id;
				} else {
					image_id = graph;
				}

				if (current_basket.hasOwnProperty('annotations')) {
					current_basket.images = [];
					current_basket.images.push(image_id);
				} else {
					current_basket = {};
					current_basket.images = [];
					current_basket.images.push(image_id);
					current_basket['id'] = collection_id;
					collections[collection_name] = current_basket;
				}
			}
			localStorage.setItem('collections', JSON.stringify(collections));
		}
	}

	update_collection_counter();
	return true;
}

function notify(msg, status) {

	var running = running || true;

	if (running) {
		clearInterval(timeout);
		$('#status').remove();
	}

	var status_element = $('#status');

	if (!status_element.length) {
		status_element = $('<div id="status">');
		$('body').append(status_element.hide());
	}

	status_element.css('z-index', 5000);
	status_class = status ? ' alert-' + status : '';
	status_element.attr('class', 'alert' + status_class);

	if (status == 'success') {
		status_element.html("<a style='color:#468847;' href='/digipal/collection'>" + msg + "</a>").fadeIn();
	} else {
		status_element.html(msg).fadeIn();
	}

	var timeout =
		setTimeout(function() {
			status_element.fadeOut();
			running = false;
		}, 5000);
}

(function() {
	update_collection_counter();
})();