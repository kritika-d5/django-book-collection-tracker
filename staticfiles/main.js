document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navActions = document.querySelector('.nav-actions');

    if (toggle && navLinks) {
        toggle.addEventListener('click', function () {
            navLinks.classList.toggle('is-open');
            if (navActions) {
                navActions.classList.toggle('is-open');
            }
        });
    }

    document.querySelectorAll('[data-reply-toggle]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const formId = btn.getAttribute('data-reply-toggle');
            const form = document.getElementById(formId);
            if (form) {
                form.classList.toggle('is-open');
            }
        });
    });
});
