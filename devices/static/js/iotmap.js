/* IoT Analyzer — Leaflet dark map helper */
(function (global) {
  'use strict';
  var STATUS_HEX = { online: '#00ff88', offline: '#4a5568', error: '#ff4444', maintenance: '#ffaa00' };

  function pinIcon(color) {
    return L.divIcon({
      className: '',
      html: '<div class="map-pin" style="width:16px;height:16px;background:' + color +
            ';color:' + color + ';"></div>',
      iconSize: [16, 16], iconAnchor: [8, 8], popupAnchor: [0, -10]
    });
  }

  function render(elId, devices, opts) {
    if (!global.L) { console.warn('Leaflet not loaded'); return; }
    opts = opts || {};
    var el = document.getElementById(elId);
    if (!el) return;

    var map = L.map(elId, { scrollWheelZoom: false, attributionControl: true });
    // Dark tiles (CartoDB dark matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    var pts = [];
    devices.forEach(function (d) {
      if (d.lat == null || d.lng == null) return;
      var color = STATUS_HEX[d.status] || STATUS_HEX.offline;
      var m = L.marker([d.lat, d.lng], { icon: pinIcon(color) }).addTo(map);
      var html = '<strong style="color:' + color + '">' + esc(d.name) + '</strong><br>' +
                 '<span style="color:#8899aa;font-size:12px">' + esc(d.type || '') + '</span>';
      if (d.location) html += '<br><span style="color:#8899aa;font-size:12px">📍 ' + esc(d.location) + '</span>';
      if (d.status_label) html += '<br><span style="font-size:11px;color:' + color + '">● ' + esc(d.status_label) + '</span>';
      if (d.url) html += '<br><a href="' + d.url + '" style="color:#00d4ff;font-size:12px">Open device →</a>';
      m.bindPopup(html);
      pts.push([d.lat, d.lng]);
    });

    if (pts.length === 1) {
      map.setView(pts[0], opts.zoom || 11);
    } else if (pts.length > 1) {
      map.fitBounds(pts, { padding: [40, 40], maxZoom: 12 });
    } else {
      map.setView(opts.center || [41.3111, 69.2797], opts.zoom || 6); // Tashkent default
    }
    setTimeout(function(){ map.invalidateSize(); }, 200);
    return map;
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  global.IoTMap = { render: render };
})(window);
