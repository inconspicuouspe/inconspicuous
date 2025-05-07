const logoutButton = document.querySelector("#logout-button");
logoutButton.addEventListener("click", (event) => {
    fetch("{{ url_for('logout') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            '{{ consts.FIELD_CSRF_TOKEN_HEADER }}': getCookie("{{ consts.FIELD_CSRF_TOKEN }}")
        },
        method: "POST",
    }).then(()=>{location.reload();});
})