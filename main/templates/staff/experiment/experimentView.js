axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({
        
    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{           
        experimentURL:'',   
        loading: true,   
        message: null,              
        experiment: null,
        recruitment_params:{allowed_list_users:[]},
        current_trait:{
            id:0,
            trait_id:0,
            min_value:0,
            max_vaue:0,
            include_if_in_range:true,
        },                    
        sessions:[],                       
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
    },

    methods:{       
        
        do_first_load:function(){
            tinyMCE.init({
                target: document.getElementById('id_reminderText'),
                height : "400",
                theme: "silver",
                convert_urls: false,
                plugins: "directionality,paste,searchreplace,code,link",
                toolbar: "undo redo | styleselect | forecolor | bold italic | alignleft aligncenter alignright alignjustify | outdent indent | link | code",
                directionality: "{{ directionality }}",
            });

            tinyMCE.init({
                target: document.getElementById('id_invitationText'),
                height : "400",
                theme: "silver",
                convert_urls: false,
                plugins: "directionality,paste,searchreplace,code,link",
                toolbar: "undo redo | styleselect | forecolor | bold italic | alignleft aligncenter alignright alignjustify | outdent indent | link | code",
                directionality: "{{ directionality }}",
            });

            // Prevent Bootstrap dialog from blocking focusin
            $(document).on('focusin', function(e) {
                if ($(e.target).closest(".tox-tinymce, .tox-tinymce-aux, .moxman-window, .tam-assetmanager-root").length) {
                    e.stopImmediatePropagation();
                }
            });
        },

        clearMainFormErrors:function(){
            for(var item in app.$data.experiment)
            {
                $("#id_" + item).attr("class","form-control");
                $("#id_errors_" + item).remove();
            }

            for(var item in app.$data.recruitment_params)
            {
                $("#id_" + item).attr("class","form-control");
                $("#id_errors_" + item).remove();
            }

            for(var item in app.$data.current_trait)
            {
                $("#id_" + item).attr("class","form-control");
                $("#id_errors_" + item).remove();
            }
        },

        //update recruitment display lists
        updateDisplayLists:function(errors){
            var e = app.$data.recruitment_params;

            app.$data.institutions_list=app.updateDisplayLists2(app.$data.experiment.institution_full);
            app.$data.include_institutions_list=app.updateDisplayLists2(e.institutions_include_full);
            app.$data.exclude_institutions_list=app.updateDisplayLists2(e.institutions_exclude_full);
            app.$data.include_experiments_list=app.updateDisplayLists2(e.experiments_include_full);
            app.$data.exclude_experiments_list=app.updateDisplayLists2(e.experiments_exclude_full);
            app.$data.include_schools_list=app.updateDisplayLists2(e.schools_include_full);
            app.$data.exclude_schools_list=app.updateDisplayLists2(e.schools_exclude_full);
            app.$data.genders_list=app.updateDisplayLists2(e.gender_full);
            app.$data.subject_type_list=app.updateDisplayLists2(e.subject_type_full);
            app.$data.trait_constraint_list=app.updateDisplayLists2(e.trait_constraints);
            app.$data.experiment.showUpFee =  parseFloat(app.$data.experiment.showUpFee).toFixed(2); 
        },

        //update recruitment display lists
        updateDisplayLists2:function(list){
            str="";

            if(list.length == 0)
            {
                str = "---"
            }   
            else
            {
                for(var i=0;i<list.length;i++)
                {
                    if(i>=1) str += " | ";
                    str += list[i].name;
                }
            }                         

            return str;
        },

        //get experiment info from server
        getExperiment: function(){
            axios.post('/experiment/{{id}}/', {
                    status:"get",                                                              
                })
                .then(function (response) {                                   
                    // app.$data.institutions= response.data.institutions; 
                    app.$data.experiment =  response.data.experiment;     
                    app.$data.sessions = response.data.sessions.experiment_sessions;      
                    app.$data.parameters = response.data.parameters;  
                    app.$data.recruitment_params = response.data.recruitment_params;                                        
                    app.$data.loading=false; 
                    app.updateDisplayLists();

                    if(!app.$data.first_load)
                    {   
                        setTimeout(app.do_first_load, 250);
                        app.$data.first_load = true;
                    }
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
                });                        
        },

        //display form errors
        displayErrors:function(errors){
            for(var e in errors)
            {
                $("#id_" + e).attr("class","form-control is-invalid")
                var str='<span id=id_errors_'+ e +' class="text-danger">';
                
                for(var i in errors[e])
                {
                    str +=errors[e][i] + '<br>';
                }

                str+='</span>';
                $("#div_id_" + e).append(str); 

                var elmnt = document.getElementById("div_id_" + e);
                elmnt.scrollIntoView(); 

                //scroll error into view
                if(e == "institution")
                {
                    var myElement = document.getElementById('id_errors_institution');
                    var topPos = myElement.offsetTop;
                    document.getElementById('institution_list_area').scrollTop = topPos;
                }

            }
        },                   

        //update experiment parameters
        updateExperiment1: function(){

            app.$data.cancelModal=false;  

            document.getElementById('id_invitationText').value = tinymce.get("id_invitationText").getContent();
            document.getElementById('id_reminderText').value = tinymce.get("id_reminderText").getContent();
            
            axios.post('/experiment/{{id}}/', {
                    status :"update1" ,                                
                    formData : $("#mainForm1").serializeArray(),                                                              
                })
                .then(function (response) {     
                                                   
                    status=response.data.status;                               

                    app.clearMainFormErrors();

                    if(status=="success")
                    {                                 
                        app.$data.experiment =  response.data.experiment;  
                        app.updateDisplayLists();
                        $('#setupModalCenter').modal('toggle');
                    }
                    else
                    {      
                        app.$data.cancelModal=true;                          
                        app.displayErrors(response.data.errors);
                    }          

                    app.$data.buttonText1="Update"                      
                })
                .catch(function (error) {
                    console.log(error);
                    app.$data.searching=false;
                });                        
        },

        //add new session to experiment
        addSession: function(){
            app.$data.addSessionButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experiment/{{id}}/', {
                    status :"add" ,                                                                                                                              
                })
                .then(function (response) {                                   
                    //redirect to new session     

                    app.$data.sessions = response.data.sessions.experiment_sessions;
                    app.$data.addSessionButtonText ='Add <i class="fas fa-plus fa-xs"></i>';
                    app.$data.addSessionErrorText = response.data.status;

                    //window.location.href = response.data.url;            
                })
                .catch(function (error) {
                    console.log(error);
                    app.$data.searching=false;
                });
        },

        //remove session from experiment
        removeSession: function(sid){
            if(confirm("Delete session?")){
                axios.post('/experiment/{{id}}/', {
                        status : "remove" ,
                        sid : sid,                                                                                                                              
                    })
                    .then(function (response) {                                   
                        
                        app.$data.sessions = response.data.sessions.experiment_sessions;            
                    })
                    .catch(function (error) {
                        console.log(error);
                    });
            }
        },

        //add trait
        addTrait:function(){
            app.$data.addTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "addTrait" ,                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    app.$data.recruitment_params = response.data.recruitment_params;  
                    app.updateDisplayLists();      
                    app.$data.addTraitButtonText = 'Add <i class="fas fa-plus fa-xs"></i>'; 
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //update trait
        updateTrait:function(){
            app.$data.updateTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "updateTrait",
                    trait_id:app.$data.current_trait.id,
                    formData : $("#traitConstraintForm").serializeArray(),                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    status=response.data.status;                               

                    app.clearMainFormErrors();

                    if(status=="success")
                    {
                        app.$data.recruitment_params = response.data.recruitment_params;  
                        app.updateDisplayLists();   
                        $('#updateTraitModal').modal('toggle');   
                    }
                    else
                    {
                        app.$data.cancelModal=true;                           
                        app.displayErrors(response.data.errors);
                    }

                    app.$data.updateTraitButtonText = 'Update <i class="fas fa-sign-in-alt"></i>'; 
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //delete trait
        deleteTrait:function(id){
            
            axios.post('/experiment/{{id}}/', {
                    status : "deleteTrait", 
                    id:id,                                                                                                                                                            
                })
                .then(function (response) {                                   
                    
                    app.$data.recruitment_params = response.data.recruitment_params;  
                    app.updateDisplayLists();       
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //update require all trait constraints
        updateRequireAllTraitContraints:function(){
            axios.post('/experiment/{{id}}/', {
                    status : "updateRequireAllTraitContraints", 
                    value: app.$data.recruitment_params.trait_constraints_require_all,                                                                                                                                                            
                })
                .then(function (response) {                                   
                    
                    app.$data.recruitment_params = response.data.recruitment_params;         
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //format date to human readable
        formatDate: function(value,date_only){
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
        checkToday: function(value1){
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
        mainFormChange1:function(){
            app.$data.buttonText1="Update *";
        },

        //put * notification on update button on change of recruitment form
        recruitmentFormChange:function(){
            app.$data.buttonText2="Update *";
        },                   

        //fire when edit trait model needs to be shown
        showEditTraits:function(){
            // app.$data.cancelModal=true;
            // app.$data.recruitmentParamsBeforeEdit = Object.assign({}, app.$data.recruitment_params);
            $('#editTraitsModal').modal('show');
            //app.clearMainFormErrors();
        },

        //fire when hide edit traits
        hideEditTraits:function(){
            // if(app.$data.cancelModal)
            // {
            //     Object.assign(app.$data.recruitment_params, app.$data.recruitmentParamsBeforeEdit);
            //     app.$data.recruitmentParamsBeforeEdit=null;
            // }
        },

        // fire when edit experiment model is shown, save copy for cancel
        showEditExperiment:function(){
            app.$data.cancelModal=true;
            app.$data.experimentBeforeEdit = Object.assign({}, app.$data.experiment);

            tinymce.get("id_reminderText").setContent(this.experiment.reminderText);
            tinymce.get("id_invitationText").setContent(this.experiment.invitationText);

            $('#setupModalCenter').modal('show');
            app.clearMainFormErrors();
            
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideEditExperiment:function(){
            if(app.$data.cancelModal)
            {
                Object.assign(app.$data.experiment, app.$data.experimentBeforeEdit);
                app.$data.experimentBeforeEdit=null;
            }
        },

        // fire when edit trait model is shown
        showUpdateTrait:function(id,index){

            tc = app.$data.recruitment_params.trait_constraints[index];

            app.$data.cancelModal=true;
            app.$data.current_trait.id = id;
            app.$data.current_trait.min_value = tc.min_value;
            app.$data.current_trait.max_value = tc.max_value;
            app.$data.current_trait.trait_id = tc.trait_id;
            app.$data.current_trait.include_if_in_range = tc.include_if_in_range;

            $('#updateTraitModal').modal('show');
            app.clearMainFormErrors();
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideUpdateTrait:function(){
            if(app.$data.cancelModal)
            {
               
            }
        },

        // fire when edit experiment model is shown, save copy for cancel
        showEditRecruitment:function(){
            // app.$data.cancelModal=true;
            // app.$data.recruitment_paramsBeforeEdit = Object.assign({}, app.$data.recruitment_params);
            // $('#recruitmentModalCenter').modal('show');
            // app.clearMainFormErrors();
            window.open("{%url 'experimentParametersView' id %}","_self");
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideEditRecruitment:function(){
            if(app.$data.cancelModal)
            {
                Object.assign(app.$data.recruitment_params, app.$data.recruitment_paramsBeforeEdit);
                app.$data.experiment.experimentBeforeEdit=null;
            }
        },

        //fire when the edit session button is pressed
        editSession:function(id)
        {
            window.open('/experimentSession/' + id,"_self");
        },

        //fill parameters with default reminder
        fillWithDefaultReminder:function(){
            app.$data.fillDefaultReminderButtonText='<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "fillDefaultReminderText",                                                                                                                                                           
                })
                .then(function (response) {                                   
                    
                    app.$data.experiment.reminderText = response.data.text;  
                    app.$data.fillDefaultReminderButtonText = 'Default Reminder <i class="fa fa-arrow-up" aria-hidden="true"></i>'; 
                    tinymce.get("id_reminderText").setContent(app.$data.experiment.reminderText);      
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //fill invitation text from template
        fillInvitationTextFromTemplate:function(){
            app.$data.fillInvitationFromTemplateButtonText='<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experiment/{{id}}/', {
                    status : "fillInvitationTextFromTemplate", 
                    value: app.$data.invitation_email_template,                                                                                                                                                            
                })
                .then(function (response) {                                   
                    
                    app.$data.experiment.invitationText = response.data.text;  
                    app.$data.fillInvitationFromTemplateButtonText='Fill <i class="fa fa-arrow-up" aria-hidden="true"></i>';    
                    tinymce.get("id_invitationText").setContent(app.$data.experiment.invitationText);
   
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //update require all trait constraints
        sendAddToAllowList:function(){

            app.$data.working = true;

            axios.post('{{request.get_full_path}}', {
                    status : "addToAllowList", 
                    formData : {allowed_list:app.$data.add_to_allow_list},                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    if(response.data.status=="success")
                    {
                        app.$data.recruitment_params = response.data.recruitment_params;
                        app.$data.allow_list_error = "";
                    }
                    else
                    {                 
                        app.$data.allow_list_error = "Error, ids not found: " + response.data.not_found_list;
                    }

                    app.$data.working = false;
            
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        sendClearAllowList:function(){

            app.$data.working = true;

            axios.post('{{request.get_full_path}}', {
                    status : "clearAllowList", 
                    formData : {},                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    if(response.data.status=="success")
                    {
                        app.$data.recruitment_params = response.data.recruitment_params;
                    }
                    else
                    {                                              
                        app.displayErrors(response.data.errors);
                    }

                    app.$data.working = false;
            
                })
                .catch(function (error) {
                    console.log(error);
                });
        },

        //fire when edit trait model needs to be shown
        showEditAllowList:function(){         
            app.clearMainFormErrors();              
           
            $('#editAllowListModal').modal('show');
        },
    },

    mounted: function(){
        this.getExperiment();
        $('#setupModalCenter').on("hidden.bs.modal", this.hideEditExperiment);
        $('#recruitmentModalCenter').on("hidden.bs.modal", this.hideEditRecruitment);
        $('#editTraitsModal').on("hidden.bs.modal", this.hideEditTraits);
        $('#updateTraitModal').on("hidden.bs.modal", this.hideUpdateTrait);
    },                 

});

