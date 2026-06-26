document.getElementById('register-form').addEventListener('submit', function(e){
        e.preventDefault();

        let form = this;
        let formData = new FormData(form)
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch(form.action || window.location.href,{
            method: 'post',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            }
        })

        .then(response => response.json().then(data => ({status: response.status, body:data})))

        .then(res =>{
            if (res.status ==200 && res.body.success){
                window.location.href = res.body.redirect_url;
            }else{
                let fieldsWithNewErrors = {};
                let errors = res.body.errors
                for (let fieldName in errors){
                    let errorMessage = errors[fieldName][0].message;
                    fieldsWithNewErrors[fieldName] = true
                    console.log(fieldsWithNewErrors)

                    if (fieldName === '__all__'){
                        let nonFieldSpan = document.getElementById('non-field-errors')
                        if (nonFieldSpan.textContent !== errorMessage){
                            nonFieldSpan.textContent = errorMessage;
                        }
                    }else{
                        let errorSpan = document.getElementById(`error_${fieldName}`);
                        if (errorSpan){
                            if (errorSpan.textContent !== errorMessage){
                                errorSpan.textContent = errorMessage;
                            }
                        }
                    }
                }

                document.querySelectorAll('.error').forEach(span => {
                    let id = span.id;
                    let fieldName = id.replace('error_', '');
                    if (id === 'non-field-errors'){ 
                        fieldName = '__all__';
                        console.log('yes')
                    }
                    
                    if (!fieldsWithNewErrors[fieldName]) {
                        span.textContent = '';
                        console.log('span',span)
                    }
                });
            }

        })
        .catch(error=> console.log('Error:', error));
    });