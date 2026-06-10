document.addEventListener('DOMContentLoaded', () => {
    // We only start the tour if Shepherd is loaded
    if (typeof Shepherd === 'undefined') return;

    const tourCompleted = localStorage.getItem('microwiki_tour_completed');

    const tour = new Shepherd.Tour({
        defaultStepOptions: {
            cancelIcon: { enabled: true },
            classes: 'premium-tooltip',
            scrollTo: { behavior: 'smooth', block: 'center' }
        },
        useModalOverlay: true
    });

    tour.addStep({
        id: 'step-search',
        title: 'Pesquisa Rápida',
        text: 'Encontre tudo em segundos! Digite o que precisa ou clique na barra para testar.',
        attachTo: { element: '.search-form-mini input', on: 'bottom' },
        advanceOn: { selector: '.search-form-mini input', event: 'focus' },
        buttons: [
            { text: 'Pular Tutorial', action: tour.cancel, classes: 'shepherd-button-secondary' }
        ]
    });

    tour.addStep({
        id: 'step-notif',
        title: 'Fique por Dentro!',
        text: 'Aqui ficam os avisos do sistema e pedidos de aprovação. Clique no sino para abrir o painel.',
        attachTo: { element: '#notif-btn', on: 'bottom' },
        advanceOn: { selector: '#notif-btn, #notif-btn *', event: 'click' },
        buttons: [
            { text: 'Pular Tutorial', action: tour.cancel, classes: 'shepherd-button-secondary' }
        ]
    });

    tour.addStep({
        id: 'step-profile',
        title: 'Central de Controle',
        text: 'Sua central de controle. Clique aqui para acessar seu perfil, histórico de artigos e as configurações do sistema.',
        attachTo: { element: '.profile-btn', on: 'bottom' },
        advanceOn: { selector: '.profile-btn, .profile-btn *', event: 'click' },
        buttons: [
            { text: 'Pular Tutorial', action: tour.cancel, classes: 'shepherd-button-secondary' }
        ]
    });

    const finishTour = () => {
        localStorage.setItem('microwiki_tour_completed', 'true');
    };

    tour.on('complete', finishTour);
    tour.on('cancel', finishTour);

    const hasSearch = document.querySelector('.search-form-mini');
    
    // Auto start if not completed
    if (!tourCompleted && hasSearch) {
        setTimeout(() => {
            tour.start();
        }, 500);
    }
    
    // Auto start if forced via parameter (from Settings)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tour') === '1' && hasSearch) {
        setTimeout(() => {
            tour.start();
        }, 500);
    }
});
