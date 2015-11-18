(function (root) {
	var nojsTabs = function (opts) {
		this.opts = opts;

		var ul = document.createElement('UL');
		var tabNum = opts.tabs.children.length;

		for (var i = 0; i < tabNum; i++) {
			var tab = opts.tabs.children[i];

			ul.appendChild(this.createTab(tab));
		}

		opts.tabBar.appendChild(ul);

		this.init();
	};

	nojsTabs.Version = '0.1.0';

	nojsTabs.prototype.createTab = function (tab) {
		var li = document.createElement('LI');
		li.id = 'tab-anchor-' + tab.id;
		
		var a = document.createElement('A');
		var a_text = document.createTextNode(this.getTitle(tab));

		a.href = '#' + tab.id;

		var that = this;

		a.addEventListener('click', function (e) {
			that.switchTab(tab);
		});

		a.appendChild(a_text);
		li.appendChild(a);
	
		return li;
	};

	nojsTabs.prototype.getTitle = function (tab) {
		var s = this.opts.titleSelector;

		if (typeof s === 'string' || s instanceof String)
			return tab.querySelector(s).innerHTML;

		else
			return s(tab);
	};

	nojsTabs.prototype.init = function () {
		var that = this;
		var targetTab = this.opts.tabs.children[0];

		// Find initial tab
		if (location.hash) {
				this.eachTab(function (tab) {
					if (location.hash == '#'+tab.id) {
						targetTab = tab;
						return true;
					}
				});

		} else {
			this.eachTab(function (tab) {
				if (tab.classList.contains(that.opts.activeClass)) {
					targetTab = tab;
					return true;
				}
			});
		}

		// Show/hide tabs
		this.eachTab(function (tab, i) {
			var a = that.opts.tabBar.getElementsByTagName('li')[i];

			if (targetTab.id == tab.id)
				that.activate([tab, a]);
			else
				that.deactivate([tab, a]);
		});
	};

	nojsTabs.prototype.eachTab = function (fn) {
		var tabs = this.opts.tabs.children;
		var tabNum = tabs.length;

		for (var i = 0; i < tabNum; i++) {
			if (fn(tabs[i], i))
				break;
		}
	};

	nojsTabs.prototype.switchTab = function (targetTab) {
		var that = this;
		var activeTab = this.opts.tabs.querySelector('.'+this.opts.activeClass);

		if (activeTab.id == targetTab.id)
			return;

		// beforeChange
		if (this.opts.beforeChange !== undefined)
			this.opts.beforeChange(activeTab, targetTab);

		// transition
		if (this.opts.transition !== undefined)
			this.opts.transition(activeTab, targetTab, function () {
				that.transition(activeTab, targetTab);
			});

		else
			this.transition(activeTab, targetTab);
	};

	nojsTabs.prototype.transition = function(activeTab, targetTab) {
		var activeA = document.getElementById('tab-anchor-' + activeTab.id);
		var targetA = document.getElementById('tab-anchor-' + targetTab.id);
		
		this.deactivate([activeTab, activeA]);
		this.activate([targetTab, targetA]);
		
		// afterChange
		if (this.opts.beforeChange !== undefined)
			this.opts.afterChange(targetTab, activeTab);
	};

	nojsTabs.prototype.activate = function (elems) {
		var len = elems.length;

		for (var i = 0; i < len; i++) {
			elems[i].classList.remove(this.opts.hiddenClass);
			elems[i].classList.add(this.opts.activeClass);
		}
	};

	nojsTabs.prototype.deactivate = function (elems) {
		var len = elems.length;

		for (var i = 0; i < len; i++) {
			elems[i].classList.remove(this.opts.activeClass);
			elems[i].classList.add(this.opts.hiddenClass);
		}
	};

	root.nojsTabs = function (opts) {
		return new nojsTabs(opts);
	};

})(window);
