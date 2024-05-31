"use strict;"

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],

    data(){return {
        buttonText : 'Submit <i class="fas fa-sign-in-alt"></i>',
        humanButtonText : 'Press if human <i class="far fa-user-circle"></i>',
        loginErrorText : "",
        form_ids : {{form_ids|safe}},    
        status:"update", 
        human:false,        
        profile:{
                {% for i in form_ids %}{{i}}:null,{% endfor %}        
        },      
        
        //modals
        helpModal: null,
    }},

    methods:{
        //get current, last or next month

        create:function create(){
        if(!app.human)
        {
            alert("Please confirm you are a person.");
            return;
        }

        app.buttonText = '<i class="fas fa-spinner fa-spin"></i>';
        app.loginErrorText = "";

        axios.post('/profileCreate/', {
                action :"create",
                formData : app.profile, 
                                            
            })
            .then(function (response) {     
                
                status=response.data.status;                               

                app.clearMainFormErrors();

                if(status == "error")
                {              
                //form validation error           
                app.displayErrors(response.data.errors);
                }
                else
                {
                app.status="done";

                Vue.nextTick(() => {
                    document.getElementById("idcreated").scrollIntoView();
                });
                
                }                        

                app.buttonText = 'Submit <i class="fas fa-sign-in-alt"></i>';

            })
            .catch(function (error) {
                console.log(error);                            
            });                        
        },

        showHelp:function showHelp(){                        
            app.helpModal.show();
        },

        humanChecker:function humanChecker(){
            app.humanButtonText = 'Press if human <i class="fas fa-spinner fa-spin"></i>';
            setTimeout(app.humanConfirm, 1000); 
        },

        humanConfirm:function humanConfirm(){
            app.humanButtonText = 'Thanks human <i class="fas fa-user-check"></i>';
            app.human=true;
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
                
                Vue.nextTick(() => {
                document.getElementById("div_id_" + e).scrollIntoView();
                });
            }
        },

        
    },            

    mounted(){
        Vue.nextTick(() => {
            app.helpModal = new bootstrap.Modal(document.getElementById('helpModal'), {keyboard: false});                     
        });                   
    },
}).mount('#app');