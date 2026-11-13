/* Minimal 3D: four soft shapes drift behind the card and lean toward the pointer.
   If Three.js can't load, the page works exactly the same without them. */
(function () {
  if (typeof THREE === "undefined") return;
  const canvas = document.getElementById("scene");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.z = 12;

  scene.add(new THREE.AmbientLight(0xffffff, 0.85));
  const sun = new THREE.DirectionalLight(0xffffff, 0.9);
  sun.position.set(3, 4, 6);
  scene.add(sun);

  const navy = new THREE.MeshStandardMaterial({ color: 0x14213d, roughness: 0.45, metalness: 0.2 });
  const orange = new THREE.MeshStandardMaterial({ color: 0xfca311, roughness: 0.4, metalness: 0.1 });
  const soft = new THREE.MeshStandardMaterial({ color: 0xb4bfdc, roughness: 0.5, metalness: 0.1 });

  const group = new THREE.Group();
  scene.add(group);

  // [geometry, material, x, y, z]  (x is scaled with screen width)
  const defs = [
    [new THREE.OctahedronGeometry(1.15), navy, -6.2, 2.4, -2],
    [new THREE.TorusGeometry(0.9, 0.3, 24, 64), orange, 6.4, -2.5, -1],
    [new THREE.IcosahedronGeometry(0.75, 0), soft, 5.4, 3.5, -3],
    [new THREE.BoxGeometry(0.95, 0.95, 0.95), soft, -5.6, -3.1, -1],
  ];
  const shapes = defs.map(([geo, mat, x, y, z], i) => {
    const m = new THREE.Mesh(geo, mat);
    m.userData = { x, y, z, phase: i * 1.7, sx: 0.12 + i * 0.04, sy: 0.18 - i * 0.02 };
    m.rotation.set(i, i * 0.6, 0);
    group.add(m);
    return m;
  });

  let aspect = 1, boost = 0, scaleTarget = 1;
  const mouse = { x: 0, y: 0 };
  window.addEventListener("pointermove", (e) => {
    mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouse.y = (e.clientY / window.innerHeight) * 2 - 1;
  });

  function layout() {
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    aspect = w / h;
    camera.aspect = aspect;
    camera.updateProjectionMatrix();
    const k = Math.min(1, aspect / 1.6);           // pull shapes inward on narrow screens
    const size = aspect < 0.8 ? 0.7 : 1;
    shapes.forEach((m) => {
      m.position.set(m.userData.x * k, m.userData.y, m.userData.z);
      m.scale.setScalar(size);
    });
    if (reduceMotion) renderer.render(scene, camera);
  }
  window.addEventListener("resize", layout);
  layout();

  const clock = new THREE.Clock();
  (function frame() {
    if (reduceMotion) return;
    const dt = Math.min(clock.getDelta(), 0.05), t = clock.elapsedTime;
    boost *= 0.96;
    shapes.forEach((m) => {
      const u = m.userData;
      m.rotation.x += dt * (u.sx + boost * 0.4);
      m.rotation.y += dt * (u.sy + boost * 0.5);
      m.position.y = u.y + Math.sin(t * 0.7 + u.phase) * 0.25;
    });
    group.rotation.y += (mouse.x * 0.18 - group.rotation.y) * 0.04;
    group.rotation.x += (mouse.y * 0.12 - group.rotation.x) * 0.04;
    group.scale.setScalar(group.scale.x + (scaleTarget - group.scale.x) * 0.06);
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  })();

  window.Scene3D = {
    nudge() { boost = Math.min(boost + 0.8, 3); },        // tiny spin kick while typing
    setMode(m) {
      if (m === "error") boost = 3;
      if (m === "success") { boost = 5; scaleTarget = 1.3; }
    },
  };
})();
