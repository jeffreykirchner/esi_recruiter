"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({
        
    delimiters: ['[[', ']]'],
       
    data(){return{      
        experimentURL:'',   
        loading: true,   
        message: null,              
        experiment: null,
        recruitment_params:{allowed_list_users:[]},
        current_trait:{
            id:0,
            trait:0,
            min_value:0,
            max_vaue:0,
            include_if_in_range:1,
        },                    
        sessions:[],       
        sessions_count:0,                
        institutions_list:"",
        include_institutions_list:"",
        exclude_institutions_list:"",
        include_experiments_list:"",
        exclude_experiments_list:"",
        include_schools_list:"",
        exclude_schools_list:"", 
        subject_type_list:"",
        genders_list:"",     
        trait_constraint_list:"",         
        buttonText1:"Update",
        buttonText2:"Update",     
        addSessionButtonText:'Add <i class="fas fa-plus fa-xs"></i>',
        addTraitButtonText:'Add <i class="fas fa-plus fa-xs"></i>',
        updateTraitButtonText:'Update <i class="fas fa-sign-in-alt"></i>',
        fillInvitationFromTemplateButtonText : 'Fill <i class="fa fa-arrow-up" aria-hidden="true"></i>',
        fillDefaultReminderButtonText:'Default Reminder <i class="fa fa-arrow-up" aria-hidden="true"></i>',
        errorsText:"",
        cancelModal:true,    
        recruitmentTitle:"Recruitment Parameters (default)",
        session:{confirmedCount:0},             //recruitment form parameter
        addSessionErrorText:"",  
        invitation_email_template:"{{invitationEmailTemplateForm_default}}",           //selected invitation email template 
        first_load : false,              //true after first load done
        working : false,
        add_to_allow_list:"",
        allow_list_error:"",

        //modal instances
        setupModalCenter:null,
        editTraitsModal:null,
        updateTraitModal:null,
        editAllowListModal:null,
    }},

    methods:{       
        
        do_first_load:function do_first_load(){
            tinyMCE.init({
                target: document.getElementById('id_reminderText'),
                height : "400",
                theme: "silver",
                convert_urls: false,
                promotion: false,
                plugins: "searchreplace,code,link",
                toolbar: "undo redo | styleselect | forecolor | bold italic | alignleft aligncenter alignright alignjustify | outdent indent | link | code",
            });

            tinyMCE.init({
                target: document.getElementById('id_invitationText'),
                height : "400",
                theme: "silver",
                convert_urls: false,
                promotion: false,
                plugins: "directionality,searchreplace,code,link",
                toolbar: "undo redo | styleselect | forecolor | bold italic | alignleft aligncenter alignright alignjustify | outdent indent | link | code",
                directionality: "{{ directionality }}",
            });

            // Prevent Bootstrap dialog from blocking focusin
            document.addEventListener('focusin', (e) => {
                if (e.target.closest(".tox-tinymce-aux, .moxman-window, .tam-assetmanager-root") !== null) {
                    e.stopImmediatePropagation();
                }
            });

            //setup modals
            app.setupModalCenter = bootstrap.Modal.getOrCreateInstance(document.getElementById('setupModalCenter'), {keyboard: false});
            app.editTraitsModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editTraitsModal'), {keyboard: false});
            app.updateTraitModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('updateTraitModal'), {keyboard: false});
            app.editAllowListModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editAllowListModal'), {keyboard: false});

            document.getElementById('setupModalCenter').addEventListener('hidden.bs.modal', app.hideEditExperiment);
            document.getElementById('editTraitsModal').addEventListener('hidden.bs.modal', app.hideEditTraits);
            document.getElementById('updateTraitModal').addEventListener('hidden.bs.modal', app.hideUpdateTrait);
        },

        clearMainFormErrors:function clearMainFormErrors(){
            for(let item in app.experiment)
            {
                let e = document.getElementById("id_errors_" + item);
                if(e) e.remove();
            }

            for(let item in app.recruitment_params)
            {                
                let e = document.getElementById("id_errors_" + item);
                if(e) e.remove();
            }

            for(let item in app.current_trait)
            {               
                let e = document.getElementById("id_errors_" + item);
                if(e) e.remove();
            }
        },

        //update recruitment display lists
        updateDisplayLists:function updateDisplayLists(errors){
            let e = app.recruitment_params;

            app.institutions_list=app.updateDisplayLists2(app.experiment.institution_full);
            app.include_institutions_list=app.updateDisplayLists2(e.institutions_include_full);
            app.exclude_institutions_list=app.updateDisplayLists2(e.institutions_exclude_full);
            app.include_experiments_list=app.updateDisplayLists2(e.experiments_include_full);
            app.exclude_experiments_list=app.updateDisplayLists2(e.experiments_exclude_full);
            app.include_schools_list=app.updateDisplayLists2(e.schools_include_full);
            app.exclude_schools_list=app.updateDisplayLists2(e.schools_exclude_full);
            app.genders_list=app.updateDisplayLists2(e.gender_full);
            app.subject_type_list=app.updateDisplayLists2(e.subject_type_full);
            app.trait_constraint_list=app.updateDisplayLists2(e.trait_constraints);
            app.experiment.showUpFee =  parseFloat(app.experiment.showUpFee).toFixed(2); 
        },

        //update recruitment display lists
        updateDisplayLists2:function updateDisplayLists2(list){
            let str="";

            if(list.length == 0)
            {
                str = "---"
            }   
            else
            {
                for(let i=0;i<list.length;i++)
                {
                    if(i>=1) str += " | ";
                    str += list[i].name;
                }
            }                         

            return str;
        },

        //get experiment info from server
        getExperiment: function getExperiment(){
            axios.post('/experiment/{{id}}/', {
                    status:"get",                                                              
                })
                .then(function (response) {                                   
                    // app.institutions= response.data.institutions; 
                    app.experiment =  response.data.experiment;     
                    app.sessions = response.data.sessions.experiment_sessions; 
                    app.sessions_count = response.data.sessions_count;     
                    app.parameters = response.data.parameters;  
                    app.recruitment_params = response.data.recruitment_params;                                        
                    app.loading=false; 
                    app.updateDisplayLists();

                    if(!app.first_load)
                    {   
                        Vue.nextTick(() => {
                            app.do_first_load();
                        });
                        // setTimeout(app.do_first_load, 250);
                        app.first_load = true;
                    }
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });                        
        },

        showAllSessions:function showAllSessions(){
            app.working=true; 
            axios.post('/experiment/{{id}}/', {
                status:"showAllSessions",                                                              
            })
            .then(function (response) {                                   
                app.sessions = response.data.sessions.experiment_sessions;      
                app.working=false; 
            })
            .catch(function (error) {
                console.log(error);
    
            });                        
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

        //update experiment parameters
        updateExperiment1: function updateExperiment1(){

            app.cancelModal=false;  

            // document.getElementById('id_invitationText').value = tinymce.get("id_invitationText").getContent();
            // document.getElementById('id_reminderText').value = tinymce.get("id_reminderText").getContent();

            app.experiment.invitationText = tinymce.get("id_invitationText").getContent();
            app.experiment.reminderText = tinymce.get("id_reminderText").getContent();
            
            axios.post('/experiment/{{id}}/', {
                    status :"update1" ,                                
                    formData : app.experiment,                                                            
                })
                .then(function (response) {     
                                                   
                    status=response.data.status;                               

                    app.clearMainFormErrors();

                    if(status=="success")
                    {                                 
                        app.experiment =  response.data.experiment;  
                        app.updateDisplayLists();
                        app.setupModalCenter.toggle();
                    }
                    else
                    {      
                        app.cancelModal=true;                          
                        app.displayErrors(response.data.errors);
                    }          

                    app.buttonText1="Update"                      
                })
                .catch(function (error) {
                    console.log(error);
                    app.searching=false;
                });                        
        },

        //add new session to experiment
        addSession: function addSession(){
            app.addSessionButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experiment/{{id}}/', {
                    status :"add" ,                                                                                                                              
                })
                .then(function (response) {                                   
                    //redirect to new session     

                    app.sessions = response.data.sessions.experiment_sessions;
                    app.sessions_count = response.data.sessions_count;

                    app.addSessionButtonText ='Add <i class="fas fa-plus fa-xs"></i>';
                    app.addSessionErrorText = response.data.status;

                    //window.location.href = response.data.url;            
                })
                .catch(function (error) {
                    console.log(error);
                    app.searching=false;
                });
        },

        //remove session from experiment
        removeSession: function removeSession(sid){
            app.working = true;
            if(confirm("Delete session?")){
                axios.post('/experiment/{{id}}/', {
                        status : "remove" ,
                        sid : sid,                                                                                                                              
                    })
                    .then(function (response) {                                 
                        
                        app.sessions = response.data.sessions.experiment_sessions;   
                        app.sessions_count = response.data.sessions_count;
                        
                        app.working = false;         
                    })
                    .catch(function (error) {
                        console.log(error);
                    });
            }
        },

        //add trait
        addTrait:function addTrait(){
            app.addTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "addTrait" ,                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    app.recruitment_params = response.data.recruitment_params;  
                    app.updateDisplayLists();      
                    app.addTraitButtonText = 'Add <i class="fas fa-plus fa-xs"></i>'; 
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //update trait
        updateTrait:function updateTrait(){
            app.updateTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "updateTrait",
                    trait_id:app.current_trait.id,        
                    formData : app.current_trait,                                                                                                                                                    
                })
                .then(function (response) {                                   
                    
                    status=response.data.status;                               

                    app.clearMainFormErrors();

                    if(status=="success")
                    {
                        app.recruitment_params = response.data.recruitment_params;  
                        app.updateDisplayLists();   
                        app.updateTraitModal.toggle();
                    }
                    else
                    {
                        app.cancelModal=true;                           
                        app.displayErrors(response.data.errors);
                    }

                    app.updateTraitButtonText = 'Update <i class="fas fa-sign-in-alt"></i>'; 
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //delete trait
        deleteTrait:function deleteTrait(id){
            
            axios.post('/experiment/{{id}}/', {
                    status : "deleteTrait", 
                    id:id,                                                                                                                                                            
                })
                .then(function (response) {                                   
                    
                    app.recruitment_params = response.data.recruitment_params;  
                    app.updateDisplayLists();       
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //update require all trait constraints
        updateRequireAllTraitContraints:function updateRequireAllTraitContraints(){
            axios.post('/experiment/{{id}}/', {
                    status : "updateRequireAllTraitContraints", 
                    value: app.recruitment_params.trait_constraints_require_all,                                                                                                                                                            
                })
                .then(function (response) {                                   
                    
                    app.recruitment_params = response.data.recruitment_params;         
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //format date to human readable
        formatDate: function formatDate(value,date_only){
            if (value) {
                //return value;
                //console.log(value);
                if(date_only)
                {
                    return moment(String(value)).local().format('M/D/YYYY');
                }
                else
                {
                    return moment(String(value)).local().format('M/D/YYYY, h:mm a');
                }
            }
            else{
                return "date format error";
            }
        },

        //check if date is today
        checkToday: function checkToday(value1){
            if(moment(value1).format("YYYY/MM/DD")== moment().format("YYYY/MM/DD"))
            {
                return true;
            }
            else
            {
                return false;
            }
            
        },

        //put * notification on update button on change
        mainFormChange1:function mainFormChange1(){
            app.buttonText1="Update *";
        },

        //put * notification on update button on change of recruitment form
        recruitmentFormChange:function recruitmentFormChange(){
            app.buttonText2="Update *";
        },                   

        //fire when edit trait model needs to be shown
        showEditTraits:function showEditTraits(){
            // app.cancelModal=true;
            // app.recruitmentParamsBeforeEdit = Object.assign({}, app.recruitment_params);
            app.editTraitsModal.show();
            //app.clearMainFormErrors();
        },

        //fire when hide edit traits
        hideEditTraits:function hideEditTraits(){
            // if(app.cancelModal)
            // {
            //     Object.assign(app.recruitment_params, app.recruitmentParamsBeforeEdit);
            //     app.recruitmentParamsBeforeEdit=null;
            // }
        },

        // fire when edit experiment model is shown, save copy for cancel
        showEditExperiment:function showEditExperiment(){
            app.cancelModal=true;
            app.experimentBeforeEdit = Object.assign({}, app.experiment);

            tinymce.get("id_reminderText").setContent(app.experiment.reminderText);
            tinymce.get("id_invitationText").setContent(app.experiment.invitationText);

            app.setupModalCenter.show();
            app.clearMainFormErrors();
            
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideEditExperiment:function hideEditExperiment(){
            if(app.cancelModal)
            {
                Object.assign(app.experiment, app.experimentBeforeEdit);
                app.experimentBeforeEdit=null;
            }
        },

        // fire when edit trait model is shown
        showUpdateTrait:function showUpdateTrait(id,index){

            let tc = app.recruitment_params.trait_constraints[index];

            app.cancelModal=true;
            app.current_trait.id = id;
            app.current_trait.min_value = tc.min_value;
            app.current_trait.max_value = tc.max_value;
            app.current_trait.trait = tc.trait;
            app.current_trait.include_if_in_range = tc.include_if_in_range;

            app.updateTraitModal.show();
            app.clearMainFormErrors();
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideUpdateTrait:function hideUpdateTrait(){
            if(app.cancelModal)
            {
               
            }
        },

        // fire when edit experiment model is shown, save copy for cancel
        showEditRecruitment:function showEditRecruitment(){
            window.open("{%url 'experimentParametersView' id %}","_self");
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideEditRecruitment:function hideEditRecruitment(){
            if(app.cancelModal)
            {
                Object.assign(app.recruitment_params, app.recruitment_paramsBeforeEdit);
                app.experiment.experimentBeforeEdit=null;
            }
        },

        //fire when the edit session button is pressed
        editSession:function editSession(id)
        {
            window.open('/experimentSession/' + id,"_self");
        },

        //fill parameters with default reminder
        fillWithDefaultReminder:function fillWithDefaultReminder(){
            app.fillDefaultReminderButtonText='<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "fillDefaultReminderText",                                                                                                                                                           
                })
                .then(function (response) {                                   
                    
                    app.experiment.reminderText = response.data.text;  
                    app.fillDefaultReminderButtonText = 'Default Reminder <i class="fa fa-arrow-up" aria-hidden="true"></i>'; 
                    tinymce.get("id_reminderText").setContent(app.experiment.reminderText);      
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //fill invitation text from template
        fillInvitationTextFromTemplate:function fillInvitationTextFromTemplate(){
            app.fillInvitationFromTemplateButtonText='<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "fillInvitationTextFromTemplate", 
                    value: app.invitation_email_template,                                                                                                                                                            
                })
                .then(function (response) {                                   
                    
                    app.experiment.invitationText = response.data.text;  
                    app.fillInvitationFromTemplateButtonText='Fill <i class="fa fa-arrow-up" aria-hidden="true"></i>';    
                    tinymce.get("id_invitationText").setContent(app.experiment.invitationText);
   
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //update require all trait constraints
        sendAddToAllowList:function sendAddToAllowList(){

            app.working = true;

            axios.post('{{request.get_full_path}}', {
                    status : "addToAllowList", 
                    formData : {allowed_list:app.add_to_allow_list},                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    if(response.data.status=="success")
                    {
                        app.recruitment_params = response.data.recruitment_params;
                        app.allow_list_error = "";
                    }
                    else
                    {                 
                        app.allow_list_error = "Error, ids not found: " + response.data.not_found_list;
                    }

                    app.working = false;
            
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        sendClearAllowList:function sendClearAllowList(){

            app.working = true;

            axios.post('{{request.get_full_path}}', {
                    status : "clearAllowList", 
                    formData : {},                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    if(response.data.status=="success")
                    {
                        app.recruitment_params = response.data.recruitment_params;
                    }
                    else
                    {                                              
                        app.displayErrors(response.data.errors);
                    }

                    app.working = false;
            
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //fire when edit trait model needs to be shown
        showEditAllowList:function showEditAllowList(){         
            app.clearMainFormErrors();              
           
            app.editAllowListModal.show();
        },
    },

    mounted(){
        Vue.nextTick(() => {
            app.getExperiment();
        });
    },                 

}).mount('#app');

