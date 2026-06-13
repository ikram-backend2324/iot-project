/* ============================================================
   IoT Analyzer — Shared 3D visualizations (Three.js r128)
   All scenes are responsive: they observe their host element
   and resize the renderer/camera on layout changes.
   ============================================================ */
(function (global) {
  'use strict';
  if (!global.THREE) { console.warn('THREE not loaded'); return; }
  var THREE = global.THREE;

  var STATUS_COLOR = {
    online: 0x00ff88, offline: 0x4a5568,
    error: 0xff4444, maintenance: 0xffaa00
  };
  var ACCENT = { cyan: 0x00d4ff, purple: 0x7c3aed, green: 0x00ff88, orange: 0xff6b35 };

  function makeRenderer(host) {
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(global.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 0);
    host.appendChild(renderer.domElement);
    return renderer;
  }

  function autoResize(host, renderer, camera, opts) {
    opts = opts || {};
    function resize() {
      var w = host.clientWidth || 300;
      // responsive height: shorter on small screens
      var h = opts.height || Math.max(220, Math.min(w * 0.62, opts.maxH || 460));
      if (w < 480 && !opts.height) h = Math.max(200, w * 0.8);
      renderer.setSize(w, h, false);
      renderer.domElement.style.height = h + 'px';
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    resize();
    if ('ResizeObserver' in global) {
      var ro = new ResizeObserver(resize);
      ro.observe(host);
    } else {
      global.addEventListener('resize', resize);
    }
    return resize;
  }

  function starfield(scene, count, radius) {
    var geo = new THREE.BufferGeometry();
    var pos = new Float32Array(count * 3);
    for (var i = 0; i < count; i++) {
      var r = radius * (0.6 + Math.random() * 0.6);
      var t = Math.random() * Math.PI * 2, p = Math.acos(2 * Math.random() - 1);
      pos[i*3] = r * Math.sin(p) * Math.cos(t);
      pos[i*3+1] = r * Math.sin(p) * Math.sin(t);
      pos[i*3+2] = r * Math.cos(p);
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    var mat = new THREE.PointsMaterial({ color: 0x335577, size: 0.6, transparent: true, opacity: 0.5 });
    scene.add(new THREE.Points(geo, mat));
  }

  /* ---------- Drag-to-rotate (no OrbitControls in r128 build) ---------- */
  function dragRotate(host, group) {
    var down = false, lx = 0, ly = 0, vx = 0, vy = 0;
    function start(x, y){ down = true; lx = x; ly = y; }
    function move(x, y){
      if(!down) return;
      vy = (x - lx) * 0.006; vx = (y - ly) * 0.006;
      group.rotation.y += vy; group.rotation.x += vx;
      group.rotation.x = Math.max(-1.2, Math.min(1.2, group.rotation.x));
      lx = x; ly = y;
    }
    function end(){ down = false; }
    host.addEventListener('mousedown', function(e){ start(e.clientX, e.clientY); });
    global.addEventListener('mousemove', function(e){ move(e.clientX, e.clientY); });
    global.addEventListener('mouseup', end);
    host.addEventListener('touchstart', function(e){ if(e.touches[0]) start(e.touches[0].clientX, e.touches[0].clientY); }, {passive:true});
    host.addEventListener('touchmove', function(e){ if(e.touches[0]){ move(e.touches[0].clientX, e.touches[0].clientY);} }, {passive:true});
    host.addEventListener('touchend', end);
    return function decay(){ if(!down){ group.rotation.y += vy*0.0; } };
  }

  /* ============================================================
     1) NETWORK GLOBE  — devices orbiting a glowing core.
        Used on the dashboard. Node color = device status.
     ============================================================ */
  function networkGlobe(host, devices) {
    if (!host) return;
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    camera.position.set(0, 0, 52);
    var renderer = makeRenderer(host);
    autoResize(host, renderer, camera, { maxH: 420 });
    starfield(scene, 280, 120);

    var world = new THREE.Group();
    scene.add(world);

    // Core sphere (wireframe globe)
    var coreGeo = new THREE.SphereGeometry(13, 28, 28);
    var coreMat = new THREE.MeshBasicMaterial({ color: ACCENT.cyan, wireframe: true, transparent: true, opacity: 0.18 });
    world.add(new THREE.Mesh(coreGeo, coreMat));
    var glowGeo = new THREE.SphereGeometry(9, 24, 24);
    var glowMat = new THREE.MeshBasicMaterial({ color: ACCENT.purple, transparent: true, opacity: 0.22 });
    world.add(new THREE.Mesh(glowGeo, glowMat));

    var light = new THREE.PointLight(0xffffff, 1.1); light.position.set(30, 30, 40); scene.add(light);
    scene.add(new THREE.AmbientLight(0x404a5a, 1.2));

    var nodes = [];
    var n = Math.max(devices.length, 1);
    devices.forEach(function (d, i) {
      var color = STATUS_COLOR[d.status] || STATUS_COLOR.offline;
      var phi = Math.acos(-1 + (2 * i + 1) / n);
      var theta = Math.sqrt(n * Math.PI) * phi;
      var R = 24;
      var x = R * Math.cos(theta) * Math.sin(phi);
      var y = R * Math.sin(theta) * Math.sin(phi);
      var z = R * Math.cos(phi);

      var m = new THREE.Mesh(
        new THREE.SphereGeometry(1.3, 16, 16),
        new THREE.MeshStandardMaterial({ color: color, emissive: color, emissiveIntensity: 0.6, roughness: 0.4 })
      );
      m.position.set(x, y, z);
      world.add(m);

      // connection line to core
      var lg = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0), new THREE.Vector3(x,y,z)]);
      var ll = new THREE.Line(lg, new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.25 }));
      world.add(ll);
      nodes.push({ mesh: m, base: 0.6, off: Math.random() * 6 });
    });

    if (!devices.length) {
      // single placeholder node so the scene isn't empty
      var ph = new THREE.Mesh(new THREE.SphereGeometry(1.3,16,16),
        new THREE.MeshStandardMaterial({ color: ACCENT.cyan, emissive: ACCENT.cyan, emissiveIntensity: 0.5 }));
      ph.position.set(20,0,0); world.add(ph);
    }

    dragRotate(host, world);
    var t = 0;
    (function loop(){
      requestAnimationFrame(loop);
      t += 0.01;
      world.rotation.y += 0.0025;
      nodes.forEach(function(nd){
        var s = 1 + Math.sin(t*2 + nd.off) * 0.15;
        nd.mesh.scale.setScalar(s);
        nd.mesh.material.emissiveIntensity = nd.base + Math.sin(t*2 + nd.off) * 0.25;
      });
      renderer.render(scene, camera);
    })();
  }

  /* ============================================================
     2) DEVICE MODEL — a stylised 3D model whose shape depends on
        device type, with a status-colored aura. Device pages.
     ============================================================ */
  function deviceModel(host, device) {
    if (!host) return;
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
    camera.position.set(0, 2, 16);
    var renderer = makeRenderer(host);
    autoResize(host, renderer, camera, { maxH: 360 });
    starfield(scene, 140, 80);

    scene.add(new THREE.AmbientLight(0x556070, 1.1));
    var key = new THREE.PointLight(0xffffff, 1.2); key.position.set(10, 14, 12); scene.add(key);
    var rim = new THREE.PointLight(ACCENT.cyan, 0.8); rim.position.set(-10, -4, -8); scene.add(rim);

    var color = STATUS_COLOR[device.status] || STATUS_COLOR.offline;
    var group = new THREE.Group(); scene.add(group);

    var bodyMat = new THREE.MeshStandardMaterial({ color: 0x1b2740, metalness: 0.6, roughness: 0.35, emissive: color, emissiveIntensity: 0.08 });
    var accentMat = new THREE.MeshStandardMaterial({ color: color, emissive: color, emissiveIntensity: 0.7, metalness: 0.3, roughness: 0.4 });
    var t = device.type;

    if (t === 'camera') {
      group.add(new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 5, 32), bodyMat));
      var lens = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.8, 1.4, 32), accentMat);
      lens.rotation.z = Math.PI/2; lens.position.x = 3; group.add(lens);
    } else if (t === 'gateway' || t === 'controller') {
      group.add(new THREE.Mesh(new THREE.BoxGeometry(6, 4, 1.4), bodyMat));
      for (var i=0;i<3;i++){ var a=new THREE.Mesh(new THREE.CylinderGeometry(0.12,0.12,3,8), accentMat); a.position.set(-2+i*2, 3.4, 0); group.add(a); var tip=new THREE.Mesh(new THREE.SphereGeometry(0.28,12,12),accentMat); tip.position.set(-2+i*2,4.9,0); group.add(tip);} 
    } else if (t === 'actuator') {
      group.add(new THREE.Mesh(new THREE.CylinderGeometry(1.4,1.4,5,24), bodyMat));
      var piston=new THREE.Mesh(new THREE.CylinderGeometry(0.7,0.7,3,24),accentMat); piston.position.y=3.2; group.add(piston);
    } else if (t === 'sensor') {
      group.add(new THREE.Mesh(new THREE.SphereGeometry(2.6, 32, 32), bodyMat));
      var ring=new THREE.Mesh(new THREE.TorusGeometry(3.4,0.18,16,48),accentMat); ring.rotation.x=Math.PI/2.4; group.add(ring);
    } else {
      group.add(new THREE.Mesh(new THREE.IcosahedronGeometry(2.8, 0), bodyMat));
      var ring2=new THREE.Mesh(new THREE.TorusGeometry(3.6,0.16,16,48),accentMat); group.add(ring2);
    }

    // Pulsing aura
    var aura = new THREE.Mesh(new THREE.SphereGeometry(5.2, 24, 24),
      new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.06, side: THREE.BackSide }));
    group.add(aura);

    dragRotate(host, group);
    var tt = 0;
    (function loop(){
      requestAnimationFrame(loop);
      tt += 0.015;
      group.rotation.y += 0.006;
      aura.scale.setScalar(1 + Math.sin(tt) * 0.05);
      aura.material.opacity = 0.05 + Math.abs(Math.sin(tt)) * 0.05;
      renderer.render(scene, camera);
    })();
  }

  /* ============================================================
     3) PC TOWER — animated computer with live gauges for
        temperature / RAM / storage / load. PC-check pages.
        metrics = {temp:0-100, ram:0-100, disk:0-100, load:0-100}
     ============================================================ */
  function pcTower(host, metrics) {
    if (!host) return;
    metrics = metrics || {};
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(42, 1, 0.1, 1000);
    camera.position.set(0, 1.5, 17);
    camera.lookAt(0, 0.5, 0);
    var renderer = makeRenderer(host);
    autoResize(host, renderer, camera, { maxH: 420 });
    starfield(scene, 160, 90);

    scene.add(new THREE.AmbientLight(0x8090a8, 1.4));
    var key = new THREE.PointLight(0xffffff, 1.4); key.position.set(8, 12, 18); scene.add(key);
    var fill = new THREE.PointLight(0x88bbff, 0.7); fill.position.set(-10, 2, 10); scene.add(fill);

    var group = new THREE.Group(); scene.add(group);

    function heat(v){ // 0..100 -> green->orange->red
      if (v == null) return ACCENT.cyan;
      if (v < 50) return 0x00ff88;
      if (v < 80) return 0xffaa00;
      return 0xff4444;
    }

    // ── Open case: a back panel + an edge frame so internals stay visible ──
    var CW = 7, CH = 9.5, CD = 4;  // case width, height, depth
    // Back motherboard panel (dark PCB with subtle glow)
    var mb = new THREE.Mesh(new THREE.BoxGeometry(CW - 0.6, CH - 0.6, 0.25),
      new THREE.MeshStandardMaterial({ color: 0x0c2230, emissive: 0x0c5566, emissiveIntensity: 0.22, metalness: 0.4, roughness: 0.6 }));
    mb.position.set(0, 0, -CD/2 + 0.2); group.add(mb);

    // Edge frame (wireframe-style struts) instead of a solid front
    var frameMat = new THREE.MeshStandardMaterial({ color: 0x2a3a55, metalness: 0.8, roughness: 0.3 });
    var edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(CW, CH, CD)),
      new THREE.LineBasicMaterial({ color: 0x3d5575 })
    );
    group.add(edges);
    // four corner posts for a solid feel
    [[-1,1],[1,1],[-1,-1],[1,-1]].forEach(function(s){
      var post = new THREE.Mesh(new THREE.BoxGeometry(0.22, CH, 0.22), frameMat);
      post.position.set(s[0]*(CW/2-0.11), 0, s[1]*(CD/2-0.11)); group.add(post);
    });
    // tinted glass side hint (very subtle, near edge, won't hide internals)
    var glass = new THREE.Mesh(new THREE.PlaneGeometry(CW, CH),
      new THREE.MeshStandardMaterial({ color: ACCENT.cyan, transparent: true, opacity: 0.04, side: THREE.DoubleSide }));
    glass.position.set(0, 0, CD/2); group.add(glass);

    var compZ = -CD/2 + 0.5; // components sit just in front of the motherboard

    // CPU block + heatsink (temperature) — top-left area, facing camera
    var cpuColor = heat(metrics.temp);
    var cpu = new THREE.Mesh(new THREE.BoxGeometry(2, 2, 0.7),
      new THREE.MeshStandardMaterial({ color: cpuColor, emissive: cpuColor, emissiveIntensity: 0.7, metalness: 0.3, roughness: 0.4 }));
    cpu.position.set(-1.6, 2.6, compZ + 0.4); group.add(cpu);
    for (var f=0; f<6; f++){ var fin=new THREE.Mesh(new THREE.BoxGeometry(1.9,0.1,0.7),
      new THREE.MeshStandardMaterial({color:0xaab8c8, metalness:0.85, roughness:0.25}));
      fin.position.set(-1.6, 1.95 - f*0.16, compZ + 0.4); group.add(fin); }

    // Spinning fan (load) — top-right
    var fan = new THREE.Group();
    var hub=new THREE.Mesh(new THREE.CylinderGeometry(0.35,0.35,0.35,16),
      new THREE.MeshStandardMaterial({color:0xaab8c8}));
    hub.rotation.x=Math.PI/2; fan.add(hub);
    var fanRing=new THREE.Mesh(new THREE.TorusGeometry(1.5,0.16,12,32),
      new THREE.MeshStandardMaterial({color:0x44546e, metalness:0.7, roughness:0.4}));
    fan.add(fanRing);
    for (var b=0;b<6;b++){ var blade=new THREE.Mesh(new THREE.BoxGeometry(1.3,0.5,0.05),
      new THREE.MeshStandardMaterial({color:ACCENT.cyan, emissive:ACCENT.cyan, emissiveIntensity:0.4, transparent:true, opacity:0.9}));
      blade.position.x=0.75; var pivot=new THREE.Group(); pivot.add(blade); pivot.rotation.z=(b/6)*Math.PI*2; fan.add(pivot);}
    fan.position.set(2.0, 2.4, compZ + 0.5); group.add(fan);

    // RAM sticks (memory usage -> how many lit) — middle row
    var ramPct = metrics.ram || 0;
    var litRam = Math.max(1, Math.round((ramPct/100) * 4));
    for (var r=0; r<4; r++){
      var lit = r < litRam;
      var c = lit ? heat(ramPct) : 0x2a3850;
      var stick=new THREE.Mesh(new THREE.BoxGeometry(0.4,3,0.5),
        new THREE.MeshStandardMaterial({color:c, emissive:c, emissiveIntensity: lit?0.7:0.06, metalness:0.3, roughness:0.5}));
      stick.position.set(-0.4 + r*0.7, -0.6, compZ + 0.5); group.add(stick);
    }

    // Storage drive (disk usage -> fill bar) — bottom
    var diskPct = metrics.disk || 0;
    var driveColor = heat(diskPct);
    var drive=new THREE.Mesh(new THREE.BoxGeometry(4,1,0.8),
      new THREE.MeshStandardMaterial({color:0x223049, metalness:0.6, roughness:0.45}));
    drive.position.set(-0.3, -3.4, compZ + 0.5); group.add(drive);
    var fillW = 3.8 * Math.max(0.03, (diskPct/100));
    var bar=new THREE.Mesh(new THREE.BoxGeometry(fillW,0.5,0.85),
      new THREE.MeshStandardMaterial({color:driveColor, emissive:driveColor, emissiveIntensity:0.7}));
    bar.position.set(-0.3 - (3.8 - fillW)/2, -3.4, compZ + 0.55); group.add(bar);

    var aura = new THREE.Mesh(new THREE.SphereGeometry(9, 20, 20),
      new THREE.MeshBasicMaterial({ color: heat(metrics.temp), transparent: true, opacity: 0.05, side: THREE.BackSide }));
    group.add(aura);

    dragRotate(host, group);
    var loadSpeed = 0.05 + (metrics.load || 20)/100 * 0.5;
    var tt=0;
    (function loop(){
      requestAnimationFrame(loop);
      tt += 0.02;
      group.rotation.y = Math.sin(tt * 0.3) * 0.35; // gentle sway instead of full spin so internals stay readable
      fan.rotation.z += loadSpeed;
      cpu.material.emissiveIntensity = 0.5 + Math.abs(Math.sin(tt*2))*0.4;
      aura.material.opacity = 0.04 + Math.abs(Math.sin(tt))*0.04;
      renderer.render(scene, camera);
    })();
  }

  /* ============================================================
     4) SCORE RADAR — lightweight SVG-free 3D-ish bars are handled
        in CSS; here we expose a helper to animate score fills.
     ============================================================ */
  function animateScores(root) {
    (root || document).querySelectorAll('.score-fill[data-val]').forEach(function(el){
      var v = parseInt(el.getAttribute('data-val'), 10) || 0;
      var color = v >= 75 ? '#00ff88' : v >= 45 ? '#ffaa00' : '#ff4444';
      var valEl = el.closest('.score-card') && el.closest('.score-card').querySelector('.score-val');
      if (valEl) valEl.style.color = color;
      el.style.background = 'linear-gradient(90deg,' + color + ',' + color + 'cc)';
      requestAnimationFrame(function(){ setTimeout(function(){ el.style.width = v + '%'; }, 80); });
    });
  }

  global.IoTViz = {
    networkGlobe: networkGlobe,
    deviceModel: deviceModel,
    pcTower: pcTower,
    animateScores: animateScores,
    STATUS_COLOR: STATUS_COLOR
  };
})(window);
