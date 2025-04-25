const logoutButton = document.querySelector("#logout-button");
logoutButton.addEventListener("click", (event) => {
    fetch("{{ url_for('logout') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
    }).then(location.reload);
})