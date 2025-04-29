// Vitesses de rotation par défaut
let rotationY = -0.002;
let rotationX = -0.0001;
let rotationZ = 0.00015;
let model = null; // Pour y accéder globalement


const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
const container = document.getElementById('planet-foreground');

renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

// Lumière ambiante plus subtile
const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
scene.add(ambientLight);

// Lumière directionnelle plus intense
const directionalLight = new THREE.DirectionalLight(0xffffff, 2);
directionalLight.position.set(5, 5, 5);
scene.add(directionalLight);

// Ajout d'une lumière d'accentuation
const pointLight = new THREE.PointLight(0xff4400, 1);
pointLight.position.set(-5, 0, -5);
scene.add(pointLight);

// Position de la caméra plus dynamique
camera.position.set(4, 2, 4);
camera.lookAt(0, 0, 0);



// Chargement du modèle
const loader = new THREE.GLTFLoader();
loader.load('/static/models/mars.glb', function(gltf) {
    model = gltf.scene;
    scene.add(model);
    model.position.set(0, 0, 0);
    camera.position.set(4, 2, 4);
    camera.lookAt(model.position);

    function animate() {
        requestAnimationFrame(animate);

        // Utilise les variables globales
        model.rotation.y += rotationY;
        model.rotation.x += rotationX;
        model.rotation.z += rotationZ;

        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.render(scene, camera);
    }
    animate();
}, undefined, function(error) {
    console.error(error);
});

// Redimensionnement
window.addEventListener('resize', function() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

