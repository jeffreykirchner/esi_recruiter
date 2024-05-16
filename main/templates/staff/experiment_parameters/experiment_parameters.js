"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";


var app = Vue.createApp({

    delimiters: ['[[', ']]'],
       
    data(){return{   
        experiment : null,
        recruitment_params:{                          //recruiment parameters
                gender:[],
                actual_participants:0,
                registration_cutoff:0,
                experience_min:0,
                experience_max:1000,
                experience_constraint:false,
                institutions_exclude_all:0,
                institutions_include_all:0,
                experiments_exclude_all:0,
                experiments_include_all:0,
                allow_multiple_participations:false,
                institutions_exclude:[],
                institutions_include:[],
                experiments_exclude:[],
                experiments_include:[],
                trait_constraints:[],
            },
        recruitment_parameters_form_ids: {{recruitment_parameters_form_ids|safe}},
        confirmedCount:0,
        session:{confirmedCount:0},             //recruitment form parameter
        loading:true,
        buttonText1:'Update <i class="fas fa-sign-in-alt"></i>',                 //recruitment parameters update button text                   
    }},

    methods:{     

        //remove all the form errors
        clearMainFormErrors:function clearMainFormErrors(){

            let s = app.recruitment_parameters_form_ids;
            for(var i in s)
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
                        window.open("{%url 'experimentView' experiment.id %}","_self");
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

        
        //gets experiment info from the server
        getExperiment: function getExperiment(){
            axios.post('{{ request.path }}', {
                    status:"get",                                                              
                })
                .then(function (response) {                                                                   
                   
                    app.recruitment_params = response.data.recruitment_params;    
                    app.experiment = response.data.experiment;                            
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
                document.getElementById("div_id_" + e).scrollIntoView();
            }
        },    
        
    },

    //run when vue is mounted
    mounted(){
        this.getExperiment();
    },                 

}).mount('#app');


