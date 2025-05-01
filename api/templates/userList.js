function userListSuccess(data){
    const success = data.success;
    if (!success) return;
    for (user of success.data) {
        userListDiv.append(user.username + "  ");
    }
}

const userListDiv = document.querySelector(".userList");

function userListLoad() {
    fetch("{{ url_for('get_user_list') }}")
        .then((response) => response.json()).then(userListSuccess);
}

