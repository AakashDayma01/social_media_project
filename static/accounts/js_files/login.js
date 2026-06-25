document.getElementById('login-form').addEventListener('submit', function(e){
    e.preventDefault();
    let form = this;
    let formData = new FormData(form)
    document.querySelectorAll('.error').forEach(span => span.textContent = '')
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
    fetch(form.action || window.location.href,{
    method: 'post',
    body: formData,
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken 
    }
    }) 
    .then(response => response.json().then(data => ({status: response.status,body:data})))
    .then(res =>{
    if (res.status === 200 && res.body.success){
        window.location.href = res.body.redirect_url;
    }else{
        let errors = res.body.errors
        for (let fieldName in errors){
            let errorMessage =  errors[fieldName][0].message;

            if (fieldName === '__all__'){
                document.getElementById('non-field-errors').textContent = errorMessage;
            }else{
                let errorSpan = document.getElementById(`error_${fieldName}`);
                if (errorSpan) {
                    errorSpan.textContent = errorMessage;
                }
            }
        }
    }
    })
    .catch(error => console.log('Error:', error));
});


function go_to_register(){
    window.location.href = "http://127.0.0.1:8000/register/"
}
