(function() {
	window.zwp = {};
	
	zwp.setupContentTabs = function () {
		nojsTabs({
			tabs: document.getElementById('tabs'),
			titleSelector: 'h3',
			tabBar: document.getElementById('tabbar'),
			hiddenClass: 'tab-hidden',
			activeClass: 'active',
			createElement: function(el) {
				if (el.tagName == 'UL')
					el.classList.add('nav', 'nav-tabs');

				else if(el.tagName == 'LI')
					el.setAttribute('role', 'presentation');
			},
		});
	};

	zwp.setupPartCheckBoxes = function (parts) {
		$(parts).find('table').each(function () {
			var table = this;

			$(table).find('th.checkall').each(function () {
				$(this).append(
					$('<input type="checkbox" class="checkall">').change(function () {
						var checkall = this;
						var checked = this.checked;

						$(table).find('input[type="checkbox"]').each(function () {
							if (this == checkall)
								return;

							this.checked = checked;
						});
					})
				);
			});
		});
	};

	/**
	 * Translate path from one language to another.
	 */
	zwp.translatePath = function (path, lang) {
		return '/' + lang + path.substr(3);
	};

	zwp.setFrameHeight = function (frame) {
		if (frame.contentDocument)
			frame.style.height = frame.contentDocument.body.scrollHeight + 20 + 'px';
		
		else
			frame.style.height = $(window).height() * 0.8 + 'px';
	};

	zwp.dirTree = function(ds, treeElement, contentElement, initialData) {
		var baseTitle = document.title.split('|').slice(1).join(' | ');

		function requestErrorHandler(xhr, state, error) {
			console.log('Request failed:', state, error);
		}

		function loadDir(id, url, title, pushHistory, cb) {
			console.log('load dir', url);
			$.ajax({
				url: url + '?fetch=content',
				dataType: 'html',
				error: requestErrorHandler,
				success: function (response) {
					$(contentElement).html(response);
					document.title = title + ' | ' + baseTitle;

					if ((pushHistory || pushHistory === undefined) && history.pushState) {
						console.log('update history to', url);
						history.pushState({
							ds: ds,
							id: id,
							title: title,
						}, null, url);
					}

					if (cb !== undefined)
						cb();
					
					zwp.setupContentTabs();
					zwp.setupPartCheckBoxes(contentElement);
				}
			});
		}

		window.onpopstate = function(e) {
			console.log('onpopstate!', e.state);
			
			if (e.state.ds != ds) {
				console.log('ds does not match, ignore', e.state, ds);
				return;
			}

			loadDir(e.state.id, window.location.pathname, e.state.title, false, function() {
				var tree = $(treeElement).jstree(true);
				tree.deselect_all(true);
				tree.select_node(e.state.id, true);
			});
		};

		$(document).ready(function() {
			$(treeElement + ' > *').remove();
			$(treeElement).on('changed.jstree', function (e, data) {
				console.log('something changed! nice!');
				console.log(data);

				if (data.action != 'select_node')
					return;
				
				loadDir(data.node.id, data.node.original.url, data.node.text);

			}).jstree({
				'core': {
					'themes': {
						'variant': 'large'
					},
					'data': function (node, cb) {
						if (node.id === '#') { // root
							cb.call(this, initialData);

						} else {
							var that = this;

							$.ajax({
								url: node.original.url + '?fetch=tree',
								dataType: 'json',
								error: requestErrorHandler,
								success: function (data) {
									console.log('got the result!', data);
									cb.call(that, data);
								}
							});
						}
					}
				}
			});
		});
	};
})();
