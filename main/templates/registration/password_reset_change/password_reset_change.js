"use strict;"

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],

    data() {return{
        buttonText : 'Change Password <i class="fas fa-sign-in-alt"></i>',
        messageText : "",
        changeMode:1,
        form_ids : {{form_ids|safe}},     
        password1:null,
        password2:null,                     
    }},

    methods:{
    //get current, last or next month

    change_password:function change_password(){
        app.buttonText = '<i class="fas fa-spinner fa-spin"></i>';
        app.messageText = "";

        axios.post('/accounts/passwordResetChange/{{token}}', {
                action :"change_password",
                formData : {
                password1 : app.password1,
                password2 : app.password2, 
                }
                                            
            })
            .then(function (response) {     
                
            status=response.data.status;                               

            app.clearMainFormErrors();

            if(status == "validation")
            {              
                //form validation error           
                app.displayErrors(response.data.errors);
            }
            else if(status == "error")
            {
                app.messageText = response.data.message;
            }
            else
            {
                app.changeMode = 2;
            }

            app.buttonText = 'Change Password <i class="fas fa-sign-in-alt"></i>';

            })
            .catch(function (error) {
                console.log(error);                            
            });                        
        },

    clearMainFormErrors:function clearMainFormErrors(){

        s = app.form_ids;                    
        for(let i in s)
        {
        let e = document.getElementById("id_errors_" + s[i]);
        if(e) e.remove();
        }

    },
    
    //display form errors
    displayErrors: function displayErrors(errors){
            for(let e in errors)
            {
                let str='<span id=id_errors_'+ e +' class="text-danger">';
                
                for(let i in errors[e])
                {
                    str +=errors[e][i] + '<br>';
                }

                str+='</span>';

                document.getElementById("div_id_" + e).insertAdjacentHTML('beforeend', str);
                //scroll to the last error
                let elmnt =  document.getElementById("div_id_" + e);
                if(elmnt) elmnt.scrollIntoView(); 
            }
        }, 

        
    },            

    mounted(){
                                
    },
}).mount('#app');