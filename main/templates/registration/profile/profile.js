"use strict;"

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],

    data() {return{
        buttonText : 'Update <i class="fas fa-sign-in-alt"></i>',
        form_ids : {{form_ids|safe}},    
        status: "update", 
        emailVerificationRequired: false,      
        profile:{{user.profile.json_for_profile_update|safe}},            
    }},

    methods:{
        //get current, last or next month

        update:function update(){

            app.buttonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/accounts/profile/', {
                    action :"update",
                    formData : app.profile,                              
                })
                .then(function (response) {     
                    
                    status = response.data.status;                               

                    app.clearMainFormErrors();

                    if(status == "error")
                    {              
                    //form validation error           
                    app.displayErrors(response.data.errors);
                    }
                    else
                    {
                    app.status = "done";
                    app.emailVerificationRequired = response.data.email_verification_required;
                    }                        

                    app.buttonText = 'Update <i class="fas fa-sign-in-alt"></i>';

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