document.addEventListener('DOMContentLoaded', () => {
    // Inicia o tour condicionalmente à disponibilidade da dependência Shepherd.
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
        text: 'Utilize a barra para localizar artigos rapidamente.',
        attachTo: { element: '.search-form-mini input', on: 'bottom' },
        advanceOn: { selector: '.search-form-mini input', event: 'focus' },
        buttons: [
            { text: 'Pular Tutorial', action: tour.cancel, classes: 'shepherd-button-secondary' }
        ]
    });

    tour.addStep({
        id: 'step-notif',
        title: 'Notificações',
        text: 'Acesse suas notificações do sistema e aprovações pendentes.',
        attachTo: { element: '#notif-btn', on: 'bottom' },
        advanceOn: { selector: '#notif-btn, #notif-btn *', event: 'click' },
        buttons: [
            { text: 'Pular Tutorial', action: tour.cancel, classes: 'shepherd-button-secondary' }
        ]
    });

    tour.addStep({
        id: 'step-profile',
        title: 'Central de Controle',
        text: 'Gerencie seu perfil, preferências e histórico de acesso.',
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
    
    // Inicia automaticamente o processo caso o tour não esteja concluído.
    if (!tourCompleted && hasSearch) {
        setTimeout(() => {
            tour.start();
        }, 500);
    }
    
    // Inicia automaticamente se houver parâmetro forçado nas configurações.
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tour') === '1' && hasSearch) {
        setTimeout(() => {
            tour.start();
        }, 500);
    }
});
