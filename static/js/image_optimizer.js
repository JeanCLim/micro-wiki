document.addEventListener('DOMContentLoaded', () => {
    // Inject Modal HTML into the body
    const modalHTML = `
        <div id="imageOptimizerModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999; justify-content:center; align-items:center;">
            <div style="background:#fff; padding:20px; border-radius:8px; max-width:500px; width:90%; text-align:center; font-family:sans-serif;">
                <h3 style="margin-top:0;">Otimização de Imagem Necessária</h3>
                <p>Esta imagem é muito pesada e deixará o sistema lento. Deseja que o sistema otimize a resolução automaticamente?</p>
                <div style="margin: 20px 0; max-height:300px; overflow:hidden; background:#eee; display:flex; justify-content:center; align-items:center; border-radius:4px;">
                    <img id="imageOptimizerPreview" style="max-width:100%; max-height:300px; object-fit:contain;" src="" alt="Preview" />
                </div>
                <div style="display:flex; justify-content:space-between; gap:10px;">
                    <button id="imageOptimizerCancel" style="flex:1; padding:10px; background:#ccc; border:none; border-radius:4px; cursor:pointer;">Cancelar</button>
                    <button id="imageOptimizerConfirm" style="flex:1; padding:10px; background:#4CAF50; color:#fff; border:none; border-radius:4px; cursor:pointer;">Confirmar e Enviar</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const modal = document.getElementById('imageOptimizerModal');
    const preview = document.getElementById('imageOptimizerPreview');
    const btnCancel = document.getElementById('imageOptimizerCancel');
    const btnConfirm = document.getElementById('imageOptimizerConfirm');

    // Attach to all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            const coverInput = form.querySelector('input[name="cover_image"]');
            if (!coverInput || !coverInput.files || coverInput.files.length === 0) {
                return; // Nothing to optimize
            }
            
            const file = coverInput.files[0];
            const MAX_SIZE = 2 * 1024 * 1024; // 2MB
            
            if (file.type.startsWith('image/') && file.size > MAX_SIZE) {
                // If we already optimized it, skip
                if (coverInput.dataset.optimized === "true") {
                    return;
                }

                e.preventDefault(); // Stop standard submission
                
                try {
                    const compressedBlob = await compressImage(file);
                    
                    // Show preview
                    preview.src = URL.createObjectURL(compressedBlob);
                    modal.style.display = 'flex';
                    
                    // Handle buttons
                    btnCancel.onclick = () => {
                        modal.style.display = 'none';
                        coverInput.value = ''; // clear
                    };
                    
                    btnConfirm.onclick = () => {
                        modal.style.display = 'none';
                        const dataTransfer = new DataTransfer();
                        const newFile = new File([compressedBlob], file.name, { type: 'image/jpeg' });
                        dataTransfer.items.add(newFile);
                        coverInput.files = dataTransfer.files;
                        coverInput.dataset.optimized = "true";
                        
                        // Resubmit form
                        form.submit();
                        // For AJAX forms, we might need a dispatchEvent or just submit.
                    };
                } catch (err) {
                    console.error("Erro na compressão: ", err);
                    alert("Ocorreu um erro ao comprimir a imagem.");
                }
            }
        });
    });
});

function compressImage(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = event => {
            const img = new Image();
            img.src = event.target.result;
            img.onload = () => {
                const canvas = document.createElement('canvas');
                const MAX_WIDTH = 1920;
                const MAX_HEIGHT = 1080;
                let width = img.width;
                let height = img.height;

                if (width > height) {
                    if (width > MAX_WIDTH) {
                        height *= MAX_WIDTH / width;
                        width = MAX_WIDTH;
                    }
                } else {
                    if (height > MAX_HEIGHT) {
                        width *= MAX_HEIGHT / height;
                        height = MAX_HEIGHT;
                    }
                }

                canvas.width = width;
                canvas.height = height;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                // Compress to JPEG with 0.8 quality
                canvas.toBlob(blob => {
                    if (blob) {
                        resolve(blob);
                    } else {
                        reject(new Error("Canvas to Blob failed"));
                    }
                }, 'image/jpeg', 0.8);
            };
            img.onerror = error => reject(error);
        };
        reader.onerror = error => reject(error);
    });
}
