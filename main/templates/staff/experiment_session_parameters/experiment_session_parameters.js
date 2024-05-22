"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],
     
    data(){return{       
        session : null,
        recruitment_params:{                          //recruiment parameters
                gender:[],
                actual_participants:0,
                registration_cutoff:0,
                experience_min:0,
                experience_max:1000,
                experience_constraint:0,
                institutions_exclude_all:0,
                institutions_include_all:0,
                experiments_exclude_all:0,
                experiments_include_all:0,
                allow_multiple_participations:0,
                institutions_exclude:[],
                institutions_include:[],
                experiments_exclude:[],
                experiments_include:[],
                trait_constraints:[],
            },
        confirmedCount:0,
        loading:true,
        recruitment_parameters_form_ids: {{recruitment_parameters_form_ids|safe}},
        buttonText1:'Update <i class="fas fa-sign-in-alt"></i>',                 //recruitment parameters update button text                   
    }},

    methods:{     

        //remove all the form errors
        clearMainFormErrors:function clearMainFormErrors(){

            let s = app.recruitment_parameters_form_ids;
            for(let i in s)
            {
                let e = document.getElementById("id_errors_" + s[i]);
                if(e) e.remove();
            }
        },

        //update recruitment parameters 
        updateRecruitmentParameters: function updateRecruitmentParameters(){                       
            axios.post('{{ request.path }}', {
                    status :"updateRecruitmentParameters" ,                                
                    formData : app.recruitment_params,                                                              
                })
                .then(function (response) {     
                                                                           
                    status=response.data.status; 
                    app.clearMainFormErrors();

                    if(status=="success")
                    {                                 
                        window.open("{%url 'experimentSessionView' session.id %}", "_self");
                    }
                    else
                    {                                
                        app.displayErrors(response.data.errors);
                    }          

                    app.buttonText1='Update <i class="fas fa-sign-in-alt"></i>';                      
                })
                .catch(function (error) {
                    console.log(error);
                    app.searching=false;
                });                        
            },

        
        //gets session info from the server
        getSession: function getSession(){
            axios.post('{{ request.path }}', {
                    status:"get",                                                              
                })
                .then(function (response) {                                                                   
                   
                    app.recruitment_params = response.data.recruitment_params;    
                    app.session = response.data.session;                            
                    app.loading = false;
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });                        
        },

        //if form is changed add * to button
        recruitmentFormChange:function recruitmentFormChange(){
            app.buttonText1='Update <i class="fas fa-sign-in-alt"></i> *';
        },

        //displays to the form errors
        displayErrors:function displayErrors(errors){
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

    //run when vue is mounted
    mounted(){
        Vue.nextTick(() => {
            app.getSession();
        });
    },                 

}).mount('#app');


