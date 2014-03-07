/**
 * function to update the dialog
   -- Digipal Project --> digipal.eu
 */

/**
 * The function update_dialog() allows to update the current content of the a dialog.
 * It requires two parameters:
 *	@prefix: a prefix for unifying DOM elements, can be an empty string
 *	@data: an array which contains two objects: allographs and features: this array has to be obtained
 *		from the function get_features() in annotation.py
 */

function update_dialog(prefix, data, selectedAnnotations, callback) {
	console.log(data);
	var s = '<div id="box_features_container">';
	var array_features_owned = features_saved(null, data['features']);
	var allographs = data['allographs'];
	if (!allographs.length) {
		s += '<p class="component" style="margin:0;">No common components</p>';
	} else {
		$.each(allographs, function(idx) {
			component = allographs[idx].name;
			component_id = allographs[idx].id;
			var features = allographs[idx].features;
			s += "<div class='component_labels' data-id='" + prefix + "component_" + component_id + "' style='border-bottom:1px solid #ccc'><b>" + component + " <span class='arrow_component fa fa-angle-double-down'></span></b>";

			s += "<div class='checkboxes_div btn-group'><span data-toggle='tooltip' data-container='body'  title='Check all' data-component = '" + component_id + "' class='check_all btn btn-xs btn-default'><i class='fa fa-check-square-o'></i></span> <span title='Unheck all' data-toggle='tooltip' data-container='body' data-component = '" + component_id + "' class='uncheck_all btn btn-xs btn-default'><i class='fa fa-square-o'></i></span></div></div>";

			s += "<div id='" + prefix + "component_" + component_id + "' data-hidden='false' class='feature_containers'>";

			$.each(features, function(idx) {
				var value = component_id + '::' + features[idx].id;
				var id = component_id + '_' + features[idx].id;
				var names = component + ':' + features[idx].name;
				s += '<div class="row row-no-margin">';

				if (typeof annotator !== 'undefined') {
					if (typeof annotator.selectedFeature !== "undefined" && annotator.selectedFeature !== null && annotator.selectedFeature.state == 'Insert') {
						array_features_owned = annotator.selectedFeature.features;
						names = value;
					}
					if (array_features_owned.indexOf(names) >= 0) {
						s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' checked /> ";
					} else {
						s += "<p class='col-md-2'><input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' /> ";
					}
					s += "<p class='col-md-10'><label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
				} else {
					if (array_features_owned.indexOf(names) >= 0) {
						s += "<p class='col-md-2'> <input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "' checked />";
					} else {
						s += "<p class='col-md-2'> <input id='" + id + "' type='checkbox' value='" + value + "' class='features_box' data-feature = '" + features[idx].id + "'/>";
					}

					s += "<p class='col-md-10'><label style='font-size:12px;display:inline;vertical-align:bottom;' for='" + id + "'>" + features[idx].name + "</label></p>";
				}

				s += '</div>';
			});

			s += "</div>";
		});
	}

	s += "</div>";
	if (callback) {
		callback(s);
	}
}

/*

Function to get the features of a described allograph
@params feature selected, url
*/

function features_saved(selectedFeature, features) {
	var array_features_owned = [];
	if (features && features.length) {
		for (var i = 0; i < features.length; i++) {
			for (var j = 0; j < features[i].feature.length; j++) {
				s = features[i].name;
				s += ':' + features[i].feature[j];
				array_features_owned.push(s);
			}
			s = '';
		}
	}
	return array_features_owned;
}


var load_group = function(group_element, cache, only_features, callback) {

	$('#show_summary').after(" <img id='allographs_loader_gif' src='/static/digipal/images/ajax-loader3.gif' />");

	var graphs, graph, url, graphs_list = [];
	var content_type = 'graph';
	graphs = group_element.find('a[data-graph]');
	$.each(graphs, function() {
		graph = $(this).data('graph');
		if (!cache.cache.graphs.hasOwnProperty(graph)) {
			graphs_list.push(graph);
		}
	});

	reload_cache(graphs_list, cache, only_features, callback);

};

var reload_cache = function(graphs, cache, only_features, callback) {
	var request, url, content_type = 'graph';
	url = "/digipal/api/" + content_type + '/' + graphs.toString() + '/';
	if (only_features) {
		url += 'features';
	}
	request = $.getJSON(url);
	request.done(function(data) {
		$("#allographs_loader_gif").remove();
		for (var i = 0; i < data.length; i++) {
			console.log(data[i]);
			var graph = graphs[i];
			var allograph = data[i]['allograph_id'];
			if (!cache.search("allograph", allograph)) {
				cache.update('allograph', allograph, data[i]);
			}

			if (!cache.search("graph", graph)) {
				cache.update('graph', graph, data[i]);
				self.dialog.temp.graph = graph;
			}
		}

		if (callback) {
			callback(data);
		}
	});
};

var get_graph = function(data, cache) {

	var graph, result = {};
	var graphs = cache.graphs;

	for (var i = 0; i < data.length; i++) {
		for (var c in graphs) {
			if (data[i].vector_id == graphs[c].vector_id) {
				graph = graphs[c];
				break;
			}
		}
	}

	result['allographs'] = cache.allographs[graph.allograph_id];
	result['features'] = graph['features'];
	result['allograph_id'] = graph.allograph_id;
	result['hand_id'] = graph['hand_id'];
	result['hands'] = graph['hands'];
	return result;

};


function intersect(a, b) {
	var intersection = [].concat(a);
	var temp = [];

	for (var i = 0; i < b.length; i++) {
		if (intersection.indexOf(b[i]) < 0) {
			temp.push(b[i]);
		}
	}

	for (i = 0; i < intersection.length; i++) {
		if (b.indexOf(intersection[i]) < 0) {
			temp.push(intersection[i]);
		}
	}

	for (i = 0; i < intersection.length; i++) {
		for (var g = 0; g < temp.length; g++) {
			if (temp[g] == intersection[i]) {
				intersection.splice(i, 1);
				i--;
			}
		}
	}

	return intersection;
}

function common_components(selectedAnnotations, cacheAnnotations, data) {
	var allograph_id, allograph, allographs, allograph_names = [],
		cacheAnn = [];

	var ind = 0;
	while (ind < selectedAnnotations.length) {
		if (typeof cacheAnnotations.graphs[selectedAnnotations[ind]] !== 'undefined') {
			allograph_id = cacheAnnotations.graphs[selectedAnnotations[ind]].allograph_id;
			allographs = $.extend({}, cacheAnnotations.allographs[allograph_id]);
			cacheAnn.push(allographs);
		}
		ind++;
	}

	var copy_data = data.slice(0);
	var n = 0;
	var arrays = [];

	for (var i in cacheAnn) {
		var array = [];
		if ($.isEmptyObject(cacheAnn[i])) {
			copy_data = [];
			return copy_data;
		}

		for (var a in cacheAnn[i]) {
			all = cacheAnn[i][a].name;
			array.push(all);
		}

		arrays.push(array);
		n++;
	}

	var ints = arrays[0],
		intersection;
	for (var h = 0; h < arrays.length - 1; h++) {
		intersection = intersect(ints, arrays[h + 1]);
		ints = intersection;
	}

	console.log(intersection);

	for (var k = 0; k < copy_data.length; k++) {
		if (intersection.indexOf(copy_data[k].name) < 0) {
			copy_data.splice(k, 1);
			k--;
		}
	}

	//console.log('common componensts: ', temp2);
	return copy_data;
}

function preprocess_features(graphs, cache) {
	var graph, all = [],
		features, component_id;
	for (var i = 0; i < graphs.length; i++) {
		graph_id = graphs[i];
		graph = cache.graphs[graph_id];
		features = graph.features;

		obj = {
			graph: graph_id
		};

		for (var d = 0; d < features.length; d++) {
			component_id = features[d].component_id;
			obj[component_id] = {};
			obj[component_id]['features'] = [];
			for (var j = 0; j < features[d].feature.length; j++) {
				obj[component_id].features.push(features[d].feature[j]);
			}
		}
		all.push(obj);
	}
	return all;
}

function compute_features(graphs, checkboxes) {
	var iterations;

	var ticked = [],
		unticked = [],
		indeterminate = [];

	var graph, graph_next;

	$.each(checkboxes, function() {
		var checkbox = $(this);
		var label = $('label[for="' + checkbox.attr('id') + '"]');
		var val = label.text();
		var component = checkbox.val().split(':')[0];

		if (graphs.length > 1) {
			iterations = graphs.length - 1;
		} else {
			iterations = 1;
		}
		for (var i = 0; i < iterations; i++) {

			if (graphs.length > 1) {
				if (graphs[i].hasOwnProperty(component)) {
					graph = graphs[i][component].features;
				} else {
					graph = [];
				}

				if (graphs[i + 1].hasOwnProperty(component)) {
					graph_next = graphs[i + 1][component].features;
				} else {
					graph_next = [];
				}

				if (graph.indexOf(val) >= 0 && graph_next.indexOf(val) < 0 || graph.indexOf(val) < 0 && graph_next.indexOf(val) >= 0) {
					indeterminate.push(checkbox.attr('id'));
				} else if (graph.indexOf(val) >= 0 && graph_next.indexOf(val) >= 0) {
					checkbox.prop('checked', true);
					checkbox.prop('indeterminate', false);
					ticked.push(val);
				} else {
					checkbox.prop('checked', false);
					checkbox.prop('indeterminate', false);
					unticked.push(val);
				}

			} else if (graphs.length == 1) {
				if (!graphs[0].hasOwnProperty(component) || typeof graphs[0][component].features == 'undefined') {
					graph = [];
				} else {
					graph = graphs[0][component].features;
				}

				if (graph.indexOf(val) >= 0) {
					checkbox.prop('checked', true);
				} else {
					checkbox.prop('checked', false);
				}

				checkbox.prop('indeterminate', false);
			} else {
				return false;
			}
		}

	});
	for (ind = 0; ind < indeterminate.length; ind++) {
		$('#' + indeterminate[ind]).prop('indeterminate', true);
	}
}

function detect_common_features(selectedAnnotations, checkboxes, cache) {
	var features_preprocessed = preprocess_features(selectedAnnotations, cache);
	compute_features(features_preprocessed, checkboxes);
	checkboxes.on('change', function() {
		var state = $(this).data('state');
		if (!state) {
			state = 1;
			$(this).data('state', state);
		} else if (state < 2) {
			state += 1;
			$(this).data('state', state);
		} else if (state === 2) {
			$(this).prop('indeterminate', true);
			state = 0;
			$(this).data('state', state);
		}
	});
}


function updateStatus(msg, status) {
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

	status_element.html(msg).fadeIn();


	var timeout =
		setTimeout(function() {
			status_element.fadeOut();
			running = false;
		}, 5000);
	//
	// GN: bugfix, JIRA 77
	// The message will push the openlayer div down and cause
	// the drawing symbol to appear below the mosue cursor.
	// To avoid this we force a render on the OL map to tell it
	// to refresh it internal location variable.
	//
	if (typeof annotator !== 'undefined') {
		annotator.map.render(annotator.map.div);
	}
}