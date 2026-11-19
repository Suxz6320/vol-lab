/**
 * VolleyLab 3D 教学模块 v2 — 用 XHR 加载 GLB（兼容 file:// 协议）
 *
 * 依赖（按顺序加载，全局 THREE 对象）：
 *   <script src="vendor/three.min.js"></script>
 *   <script src="vendor/OrbitControls.js"></script>
 *   <script src="vendor/GLTFLoader.js"></script>
 *   <script src="vendor/skill-3d.js"></script>
 *
 * 使用：<div data-glb="models/skill-spike.glb"></div>
 */
(function () {
  if (typeof THREE === "undefined") {
    console.error("[skill-3d] THREE.js not loaded");
    return;
  }

  document.querySelectorAll("[data-glb]").forEach(function (container) {
    var glbPath = container.dataset.glb;
    if (!glbPath) return;
    initScene(container, glbPath);
  });

  function loadGLB(url, onSuccess, onProgress, onError) {
    /**
     * 用 XMLHttpRequest 加载 GLB 为 ArrayBuffer，兼容 file:// 协议
     * （fetch() 在 file:// 下被 CORS 拦，但 XHR 通常允许读本地文件）
     */
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.responseType = "arraybuffer";
    xhr.onload = function () {
      if (xhr.status === 200 || xhr.status === 0) {
        // status=0 是 file:// 协议下的正常返回
        onSuccess(xhr.response);
      } else {
        onError(new Error("HTTP " + xhr.status));
      }
    };
    xhr.onprogress = function (e) {
      if (e.lengthComputable && onProgress) {
        onProgress(e.loaded, e.total);
      }
    };
    xhr.onerror = function () {
      // file:// 下有时 status 也不可靠，检查 response 是否存在
      if (xhr.response && xhr.response.byteLength > 0) {
        onSuccess(xhr.response);
      } else {
        onError(new Error("XHR error for " + url));
      }
    };
    xhr.send();
  }

  function initScene(container, glbPath) {
    var width = container.clientWidth || 400;
    var height = container.clientHeight || 300;

    var scene = new THREE.Scene();
    scene.background = new THREE.Color(0x171D26);

    var camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 100);
    camera.position.set(2.2, 1.6, 2.2);

    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    // Lights
    scene.add(new THREE.HemisphereLight(0x404a55, 0x0e1217, 0.7));
    var dir = new THREE.DirectionalLight(0xffffff, 1.0);
    dir.position.set(5, 8, 4);
    scene.add(dir);
    var fill = new THREE.DirectionalLight(0xaac4e0, 0.4);
    fill.position.set(-4, 3, -2);
    scene.add(fill);
    scene.add(new THREE.GridHelper(12, 24, 0x2A3441, 0x202832));

    // Controls
    var controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 0.8;
    controls.maxDistance = 8;
    controls.maxPolarAngle = Math.PI / 2 - 0.05;
    controls.target.set(0, 0.9, 0);
    controls.update();

    // Loading UI
    var loading = document.createElement("div");
    loading.style.cssText = "position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#8C98A8;font-size:13px;font-family:ui-monospace,monospace;letter-spacing:.1em;pointer-events:none;";
    loading.textContent = "加载中 3D 模型...";
    if (getComputedStyle(container).position === "static") container.style.position = "relative";
    container.appendChild(loading);

    var mixer = null;
    var loader = new THREE.GLTFLoader();

    loadGLB(
      glbPath,
      function (arrayBuffer) {
        // 手动把 ArrayBuffer 喂给 GLTFLoader.parse()
        loader.parse(
          arrayBuffer,
          "",  // path prefix（因为我们已经手动读进来了，传空字符串）
          function (gltf) {
            var model = gltf.scene;
            scene.add(model);
            loading.remove();

            // 动画播放
            if (gltf.animations && gltf.animations.length) {
              mixer = new THREE.AnimationMixer(model);
              var action = mixer.clipAction(gltf.animations[0]);
              action.setLoop(THREE.LoopRepeat);
              action.clampWhenFinished = false;
              action.timeScale = 0.55;  // 慢放适合教学
              action.play();
            }

            // 自适应相机
            var box = new THREE.Box3().setFromObject(model);
            var size = box.getSize(new THREE.Vector3());
            var center = box.getCenter(new THREE.Vector3());
            var maxDim = Math.max(size.x, size.y, size.z);
            var fov = camera.fov * Math.PI / 180;
            var cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.8;
            camera.position.set(center.x + cameraZ * 0.6, center.y + cameraZ * 0.5, center.z + cameraZ * 0.6);
            controls.target.copy(center);
            controls.update();
          },
          function (err) {
            loading.textContent = "模型解析失败";
            loading.style.color = "#E2574C";
            console.error("[skill-3d] GLTF parse error:", err);
          }
        );
      },
      function (loaded, total) {
        if (total) {
          loading.textContent = "加载中 " + Math.round((loaded / total) * 100) + "%";
        }
      },
      function (err) {
        loading.textContent = "3D 加载失败";
        loading.style.color = "#E2574C";
        console.error("[skill-3d]", err);
        // 额外诊断：列出实际尝试的路径
        console.error("[skill-3d] tried path:", glbPath, "current page:", location.href);
      }
    );

    // Render loop
    var clock = new THREE.Clock();
    var running = true;
    function animate() {
      if (!running) return;
      requestAnimationFrame(animate);
      var delta = clock.getDelta();
      if (mixer) mixer.update(delta);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();

    // Page hide / show
    document.addEventListener("visibilitychange", function () {
      running = !document.hidden;
      if (running) animate();
    });

    // Resize
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(function () {
        var w = container.clientWidth || width;
        var h = container.clientHeight || height;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
      }).observe(container);
    }
  }
})();
