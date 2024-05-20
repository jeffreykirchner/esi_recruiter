"use strict";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],
      
    data(){return{
        loading: true,   
        message: null,       
        showLoadingSpinner : true,
        searchResults:[],                       //search results for manual add
        searchText:"",
        searchAddResult:"",    
        findButtonText:"Find",   
        multiDayCount:1,
        multiDayButtonText:"Multi Day <i class='fas fa-plus fa-xs'></i>",
        inviteButtonText:"Invite <i class='fa fa-users'></i>",
        showUnconfirmedButtonText:'Show <i class="fa fa-eye fa-xs"></i>',
        cancelSessionButtonText:'Cancel Session <i class="fa fa-ban fa-xs"></i>',
        searchResultsEmptyText:"",           //show when no results found from manual add
        inviteResultsEmptyText:"",           //show when no subject fround for invitiation
        sendMessageSubject:"",               //subject of send message     
        sendMessageText:"<p>[first name],</p><p>If you have any questions contact [contact email].</p>",   //text of send message     
        emailMessageList:"",                 //emails for send message    
        sendMessageButtonText:"Send Message <i class='fas fa-envelope fa-xs'></i>", 
        reSendMessageButtonText:"Re-send <i class='fas fa-envelope fa-xs'></i>",
        session:null,                   
        recruitment_params:{allowed_list_users:[]},
        current_trait:{                   //current trait being edited
            id:0,
            trait:0,
            min_value:0,
            max_vaue:0,
            include_if_in_range:1,
        },
        recruitmentTitle:"Recruitment Parameters",
        subjectInvitations:[],                     //list of subject invitations
        subjectInvitationCount:0,                  //binding to invition count input box
        subjectInvitationList:"",                  //visable list of subject invitations
        subjectCancelationList:"",                 //visable list of subject cancelations
        currentSessionDayIndex:0,
        manualAddSendInvitation:true,              //send an invitation when manually adding subjets
        messageList:[],                            //list of email messages sent to users                      
        showMessageListButtonText:'Show <i class="fa fa-eye fa-xs"></i>',  //button text for show message list 
        invitationList:[],                         //list of invitations sent to users     
        showInvitationListButtonText:'Show <i class="fa fa-eye fa-xs"></i>',  //button text for show invitation list     
        downloadInvitationListButtonText:'Download <i class="fas fa-download"></i>',  //button text for download invitation list                          
        currentSessionDay:{{current_session_day_json|safe}},       
        currentSessionDayActionAll:false,                          //actions taken in current should optionally affect all session days           
        include_institutions_list:"",                              //display lists of parameters
        exclude_institutions_list:"",
        include_experiments_list:"",
        exclude_experiments_list:"", 
        include_schools_list:"",
        exclude_schools_list:"",
        subject_type_list:"",
        trait_constraint_list:"", 
        genders_list:"",        
        buttonText1:"Update",                 //recruitment parameters update button text
        buttonText2:"Update",                 //sesion day update button text
        updateInvitationButtonText:'Update <i class="fas fa-sign-in-alt"></i>',
        addTraitButtonText:'Add <i class="fas fa-plus fa-xs"></i>',
        updateTraitButtonText:'Update <i class="fas fa-sign-in-alt"></i>',
        subjectsCaption1:"Confirmed",
        experiment_invitation_text:"",
        invite_to_all:false,
        add_to_allow_list:"",
        allow_list_error:"",
        first_load : false,              //true after first load done   
        working : false,    
        
        //modals
        sessionModal : null,
        editSessionModal : null,
        subjectsModalCenter : null,
        inviteSubjectsModalCenter : null,
        cancelSessionModalCenter : null,
        manuallyAddSubjectsModalCenter : null,
        sendMessageModalCenter : null,
        editInvitationTextModal : null,
        editTraitsModal : null,
        updateTraitModal : null,
        editAllowListModal : null,
    }},

    methods:{ 
        do_first_load:function do_first_load(){
            tinyMCE.init({
                target: document.getElementById('id_invitationRawText'),
                height : "400",
                theme: "silver",
                convert_urls: false,
                promotion: false,
                auto_focus: 'id_invitationRawText',
                plugins: "directionality,searchreplace,code,link",
                    toolbar: "undo redo | styleselect | forecolor | bold italic | alignleft aligncenter alignright alignjustify | outdent indent | link | code",
                directionality: "{{ directionality }}",
            });
    
            tinyMCE.init({
                target: document.getElementById('sendMessageText'),
                height : "400",
                theme: "silver",
                convert_urls: false,
                promotion: false,
                auto_focus: 'id_invitationRawText',
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

            app.sessionModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('sessionModal'), {keyboard: false});
            app.editSessionModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editSessionModal'), {keyboard: false});
            app.subjectsModalCenter = bootstrap.Modal.getOrCreateInstance(document.getElementById('subjectsModalCenter'), {keyboard: false});
            app.inviteSubjectsModalCenter = bootstrap.Modal.getOrCreateInstance(document.getElementById('inviteSubjectsModalCenter'), {keyboard: false});
            app.cancelSessionModalCenter = bootstrap.Modal.getOrCreateInstance(document.getElementById('cancelSessionModalCenter'), {keyboard: false});
            app.manuallyAddSubjectsModalCenter = bootstrap.Modal.getOrCreateInstance(document.getElementById('manuallyAddSubjectsModalCenter'), {keyboard: false});
            app.sendMessageModalCenter = bootstrap.Modal.getOrCreateInstance(document.getElementById('sendMessageModalCenter'), {keyboard: false});
            app.editInvitationTextModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editInvitationTextModal'), {keyboard: false});
            app.editTraitsModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editTraitsModal'), {keyboard: false});
            app.updateTraitModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('updateTraitModal'), {keyboard: false});
            app.editAllowListModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('editAllowListModal'), {keyboard: false});

            document.getElementById('sessionModal').addEventListener('hidden.bs.modal', app.hideSetup);
            document.getElementById('editSessionModal').addEventListener('hidden.bs.modal', app.hideEditSession);
            document.getElementById('subjectsModalCenter').addEventListener('hidden.bs.modal', app.hideShowSubjects);
            document.getElementById('inviteSubjectsModalCenter').addEventListener('hidden.bs.modal', app.hideInviteSubjects);
            document.getElementById('cancelSessionModalCenter').addEventListener('hidden.bs.modal', app.hideCancelSession);
            document.getElementById('manuallyAddSubjectsModalCenter').addEventListener('hidden.bs.modal', app.hideManuallyAddSubjects);
            document.getElementById('sendMessageModalCenter').addEventListener('hidden.bs.modal', app.hideSendMessage);
            document.getElementById('editInvitationTextModal').addEventListener('hidden.bs.modal', app.hideEditInvitation);
            document.getElementById('editTraitsModal').addEventListener('hidden.bs.modal', app.hideEditTraits);
            document.getElementById('updateTraitModal').addEventListener('hidden.bs.modal', app.hideUpdateTrait);
        },    

        //remove all the form errors
        clearMainFormErrors:function clearMainFormErrors(){

            for(var item in app.currentSessionDay)
            {
                let e = document.getElementById("id_errors_" + item);
                if(e) e.remove();
            }

            for(var item in app.session)
            {
                let e = document.getElementById("id_errors_" + item);
                if(e) e.remove();
            }

            for(var item in app.current_trait)
            {
                let e = document.getElementById("id_errors_" + item);
                if(e) e.remove();
            }
        },

        //creates lists  of recruitment parameters
        updateDisplayLists:function updateDisplayLists(errors){
            let e = app.recruitment_params;
            
            app.include_institutions_list=app.updateDisplayLists2(e.institutions_include_full);
            app.exclude_institutions_list=app.updateDisplayLists2(e.institutions_exclude_full);
            app.include_experiments_list=app.updateDisplayLists2(e.experiments_include_full);
            app.exclude_experiments_list=app.updateDisplayLists2(e.experiments_exclude_full);
            app.include_schools_list=app.updateDisplayLists2(e.schools_include_full);
            app.exclude_schools_list=app.updateDisplayLists2(e.schools_exclude_full);
            app.trait_constraint_list=app.updateDisplayLists2(e.trait_constraints);
            app.genders_list=app.updateDisplayLists2(e.gender_full);
            app.subject_type_list=app.updateDisplayLists2(e.subject_type_full);
            
        },

        updateDisplayLists2:function updateDisplayLists2(list){
            let str="";

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

        //gets session info from the server
        getSession: function getSession(){
            axios.post('{{request.get_full_path}}', {
                    status:"get",                                                              
                })
                .then(function (response) {                                                                   
                    app.session= response.data.session;
                    app.experiment_invitation_text = response.data.experiment_invitation_text;
                    app.recruitment_params = response.data.recruitment_params;                                
                    app.updateDisplayLists();
                    app.showLoadingSpinner=false;
                    app.invite_to_all = response.data.invite_to_all;

                    if(app.session.canceled)
                    {
                        app.cancelSessionButtonText = "*** CANCELED ***";
                    }

                    if(!app.first_load)
                    {   
                        Vue.nextTick(function () {
                        // setTimeout(app.do_first_load, 250);
                        // 
                            app.do_first_load();
                            app.first_load = true;
                        });
                    }
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });                        
        },

        //add a new session day
        addSessionDay: function addSessionDay(){
            if(app.multiDayButtonText.includes("Multi"))
            {
                app.multiDayButtonText = '<i class="fas fa-spinner fa-spin"></i>';

                axios.post('{{request.get_full_path}}', {
                    status:"addSessionDay", 
                    count:app.multiDayCount,                                                             
                })
                .then(function (response) {                                   
                    app.session= response.data.session;  
                    app.session = response.data.session;             
                    
                    app.multiDayButtonText = "Multi Day <i class='fas fa-plus fa-xs'></i>";
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });
            }
                                    
        },

        //deletes a session day
        removeSessionDay: function removeSessionDay(id){
            if(confirm("Delete Session Day?")){
                axios.post('{{request.get_full_path}}', {
                        status:"removeSessionDay",    
                        id:id,                                                          
                    })
                    .then(function (response) {                                   
                        app.session.experiment_session_days= response.data.sessionDays.experiment_session_days;                                
                        //app.updateDisplayLists();
                    })
                    .catch(function (error) {
                        console.log(error);
                        //app.searching=false;                                                              
                    });                        
            }
        },

        //invite subjects
        inviteSubjects: function inviteSubjects(){
            if(!app.inviteButtonText.includes("Invite")) return;

            app.inviteButtonText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"inviteSubjects",     
                subjectInvitations:app.subjectInvitations,                                                                
            })
            .then(function (response) {                                   

                status = response.data.status
                app.session.experiment_session_days=response.data.es_min.experiment_session_days;
                
                app.subjectInvitations = [];                    
                app.subjectInvitationCount = 0;               
                app.subjectInvitationList = ""; 

                if(status != 'success')
                {
                    userFails = response.data.userFails;

                    for (var i = 0; i < userFails.length; i++)
                    {
                        app.subjectInvitationList += 'Failed to add user to session: ';
                        app.subjectInvitationList += '<a href = "/userInfo/' + userFails[i].id + '" target="_blank" >'; 
                        app.subjectInvitationList += userFails[i].last_name + ", " + userFails[i].first_name + "</a><br>"
                    }
                    
                    if(response.data.mailResult.error_message != "")
                    {
                        app.subjectInvitationList += "<br>Email Send Error:<br>"
                        app.subjectInvitationList += response.data.mailResult.error_message + "<br><br>";
                    }                                
                }                             
                else
                {      
                                                                
                                          
                }      
                app.subjectInvitationList +=  response.data.mailResult.mail_count + " invitations sent.";  
                app.inviteButtonText="";    
                app.session.invitationCount = response.data.invitationCount;               
                
            })
            .catch(function (error) {
                console.log(error);                                                                                        
            }); 
        },

        //find subjects to invite
        findSubjectsToInvite: function findSubjectsToInvite(){

            if(app.subjectInvitationList.includes('class')) return;

            app.subjectInvitationList='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.inviteResultsEmptyText="";

            axios.post('{{request.get_full_path}}', {
                status:"findSubjectsToInvite",    
                number:app.subjectInvitationCount,                                                          
            })
            .then(function (response) {                                   
                app.subjectInvitations = response.data.subjectInvitations;   
                
                var totalValid = response.data.totalValid;

                var s ="";
                var l = app.subjectInvitations.length

                for (var i = 0; i < l; i++) {
                    if (l > 1)
                    {
                        if(i  > 0 && i != l-1)
                            s += ", ";
                        else if(i == l-1)
                            s += " and "; 
                    }                                                                  

                    s += '<a href = "/userInfo/' + app.subjectInvitations[i].id + '" target="_blank" >';
                    s += app.subjectInvitations[i].first_name + " ";
                    s += app.subjectInvitations[i].last_name; 
                    s += "</a>";
                }

                s += "<br><br>";
                s += "<center><span style='color:gray;'>Total Found: " + totalValid + "<span><center>";

                app.subjectInvitationList = s;  
                app.inviteButtonText="Invite <i class='fa fa-users'></i>";    

                if(s=="") app.inviteResultsEmptyText="No Users Found<br><br>";                       
                //app.updateDisplayLists();
            })
            .catch(function (error) {
                console.log(error);                                                                                        
            }); 
        },

        //clear subjects to invite
        clearSubjectsToInvite: function clearSubjectsToInvite(){
            app.subjectInvitationList ="";
            app.inviteButtonText="Invite <i class='fa fa-users'></i>";   
            app.inviteResultsEmptyText="";                      
        },

        //cancel a session day (not in use)
        cancelSessionDay: function cancelSessionDay(){      
            if( app.session.canceled) return;
            if(app.subjectCancelationList=='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>') return;
            //if(app.cancelSessionButtonText == "*** CANCELED ***" ) return;

            app.subjectCancelationList='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('{{request.get_full_path}}', {
                    status:"cancelSession",   
                    //id:id,                                                           
                })
                .then(function (response) {                                   
                    app.session = response.data.session;

                    app.cancelSessionButtonText='*** CANCELED ***';

                    app.subjectCancelationList = "";

                    if(response.data.mailResult.error_message != "")
                    {
                        app.subjectCancelationList += "<br>Email Send Error:<br>"
                        app.subjectCancelationList += response.data.mailResult.error_message + "<br><br>";
                    }
                    else
                    {
                        app.subjectCancelationList +=  response.data.mailResult.mail_count + " cancelations sent.";                                     
                    }
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });                        
        },

        //update the session day parameters
        updateSessionDay: function updateSessionDay(){

            var sessionCanceledChangedMessage=false;

            if(app.currentSessionDay.canceled != 
                app.session.experiment_session_days[app.currentSessionDayIndex].canceled)
            {
                if(confirm("Send email about cancellation update?")){
                    var sessionCanceledChangedMessage=true;
                }
            }

            axios.post('{{request.get_full_path}}', {
                    status:"updateSessionDay",   
                    id:app.currentSessionDay.id, 
                    formData : app.currentSessionDay,
                    sessionCanceledChangedMessage:sessionCanceledChangedMessage,                                                          
                })
                .then(function (response) {
                    status=response.data.status;

                    app.clearMainFormErrors();

                    if(status=="success")
                    {
                        app.session.experiment_session_days = response.data.sessionDays.experiment_session_days;   
                        app.session.invitationText = response.data.invitationText;                         
                        app.cancelModal=false;
                        app.sessionModal.toggle();
                    }
                    else
                    {
                        app.displayErrors(response.data.errors);
                    }                                  
                    
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });                        
        },

        //update the session day parameters
        updateInvitationText: function updateInvitationText(){

            app.updateInvitationButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.session.invitationRawText = tinymce.get("id_invitationRawText").getContent();

            axios.post('{{request.get_full_path}}', {
                    status:"updateInvitationText",   
                    invitationRawText : app.session.invitationRawText,                                                          
                })
                .then(function (response) {
                    app.session.invitationText = response.data.invitationText;
                    
                    app.updateInvitationButtonText ='Update <i class="fas fa-sign-in-alt"></i>';
                    app.editInvitationTextModal.toggle();
                
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });                        
        },

        //fill inviation text with experiment default
        fillInvitationWithDefault:function fillInvitationWithDefault(){
            app.session.invitationRawText = app.experiment_invitation_text;
            tinymce.get("id_invitationRawText").setContent(app.session.invitationRawText);
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
                var elmnt =  document.getElementById("div_id_" + e);
                if(elmnt) elmnt.scrollIntoView();
            }
        },  

        //if form is changed add * to button
        recruitmentFormChange:function recruitmentFormChange(){
            app.buttonText1="Update *";
        },

        //if form is changed add * to button
        mainFormChange2:function mainFormChange2(){
            app.buttonText2="Update *";
        },

        // fire when edit experiment model is shown, save copy for cancel
        showEditRecruitment:function showEditRecruitment(){
            window.open("{%url 'experimentSessionParametersView' session.id %}","_self");
        },

        //fire when the run session button is pressed
        runSession:function runSession(id)
        {
            window.open('/experimentSessionRun/' + id,"_self");
        },

        //add trait
        addTrait:function addTrait(){
            app.addTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('{{request.get_full_path}}', {
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
            axios.post('{{request.get_full_path}}', {
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
            
            axios.post('{{request.get_full_path}}', {
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
            axios.post('{{request.get_full_path}}', {
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

        // fire when edit setup model is shown, save copy for cancel
        showSetup:function showSetup(id){
            app.cancelModal=true;
            app.currentSessionDay= Object.assign({},app.session.experiment_session_days[id]);
            app.currentSessionDayIndex=id;
            app.currentSessionDay.date = app.formatDateForInput(app.currentSessionDay.date_raw);
            app.currentSessionDay.reminder_time = app.formatDateForInput(app.currentSessionDay.reminder_time_raw);
            app.sessionBeforeEdit = Object.assign({}, app.session);
            app.buttonText2="Update";
            app.sessionModal.show();
            app.clearMainFormErrors();
        },

        //fire when edit setup model hides, cancel action if nessicary
        hideSetup:function hideSetup(){
            if(app.cancelModal)
            {
                Object.assign(app.session, app.sessionBeforeEdit);
                app.sessionBeforeEdit=null;                            
                app.buttonText2="Update";
            }
        },

        // fire when view subjects model is shown
        showSubjects:function showSubjects(id){
            app.cancelModal=true;
            app.currentSessionDay = Object.assign({},app.session.experiment_session_days[id]);
            app.currentSessionDayIndex =id;
            // app.sessionBeforeEdit = Object.assign({}, app.session);
            app.buttonText3="Update";
            app.subjectsModalCenter.show();
            // app.clearMainFormErrors();
        },

        //fire when view setup model closes, cancel action if nessicary
        hideShowSubjects:function hideShowSubjects(){    
            app.showUnconfirmedButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';                    
        },

        // fire when invite subjects subjects model is shown
        showInviteSubjects:function showInviteSubjects(id){                        
            app.inviteSubjectsModalCenter.show();
            app.inviteResultsEmptyText="";
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideInviteSubjects:function hideInviteSubjects(){   

            app.subjectInvitations = [];                    
            app.subjectInvitationCount = 0;               
            app.subjectInvitationList = "";    
            
            app.inviteButtonText="Invite <i class='fa fa-users'></i>";
        },

        // fire when cancel session model is shown
        showCancelSession:function showCancelSession(id){ 

            app.subjectCancelationList = "";

            let l="";
            let s="Emails will be sent to the subjects that have confirmed: <br><br>"
            let c1=app.session.experiment_session_days.length;
            let u1 = app.session.confirmedEmailList

            for(let i=0;i<u1.length;i++)
            {
                //u2 = u1[i].user;

                if (u1.length > 1)
                    {
                        if(i  > 0 && i != u1.length-1)
                            s += ", ";
                        else if(i == u1.length-1)
                            s += " and "; 
                    }                                                                  

                    s += '<a href = "/userInfo/' +u1[i].user_id + '" target="_blank" >';
                    s += u1[i].user_first_name + " ";
                    s += u1[i].user_last_name; 
                    s += "</a>";
            }

            app.subjectCancelationList = s;
            app.cancelSessionModalCenter.show();
            // app.clearMainFormErrors();
        },

        //fire when hide cancel session  model, cancel action if nessicary
        hideCancelSession:function hideCancelSession(){   

            
        },

        // fire when invite subjects subjects model is shown
        showEditInvitation:function showEditInvitation(id){    

            tinymce.get("id_invitationRawText").setContent(app.session.invitationRawText);
            app.editInvitationTextModal.show();
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideEditInvitation:function hideEditInvitation(){       
                        
        },

        //invitation text changed, put * in buttonn text
        invitationTextChange:function invitationTextChange(){
            app.updateInvitationButtonText="Update <i class='fas fa-sign-in-alt'></i> *";
        },

        // fire when invite subjects subjects model is shown
        showManuallyAddSubjects:function showManuallyAddSubjects(id){    
            app.searchAddResult="";   
            app.searchResults=[];
            app.searchText=""; 
            app.searchAddResult = "";          
            app.manuallyAddSubjectsModalCenter.show();
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideManuallyAddSubjects:function hideManuallyAddSubjects(){       
            app.searchResults=[];
            app.searchText="";  
            app.findButtonText="Find";             
        },

        // fire when invite subjects subjects model is shown
        showSendMessage:function showSendMessage(id){    

            app.emailMessageList="";
            tinymce.get("sendMessageText").setContent(app.sendMessageText);

            for(let i=0;i<app.session.confirmedEmailList.length;i++)
            {
                let v = app.session.confirmedEmailList[i];

                if(app.emailMessageList != "")
                {
                    app.emailMessageList += ", ";
                }
                
                app.emailMessageList += '<a href = "/userInfo/' + v.user_id + '" target="_blank" >';
                app.emailMessageList += v.user_email; 
                app.emailMessageList += "</a>";
            }

            app.sendMessageModalCenter.show();
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideSendMessage:function hideSendMessage(){       
            app.sendMessageText="<p>[first name],</p><p>If you have any questions contact [contact email].</p>";      
            app.emailMessageList="";    
            // app.sendMessageSubject=""; 
            app.sendMessageButtonText = "Send Message <i class='fas fa-envelope fa-xs'></i>";       
        },

        //send an email to all of the confirmed subjects
        sendEmailMessage:function sendEmailMessage(){

            if(app.sendMessageSubject == "" )
            {
                confirm("Add a subject to your message.");
                return;
            }

            if(app.sendMessageText == "" )
            {
                confirm("Your message is empty.");
                return;
            }

            if(app.sendMessageButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.sendMessageText = tinymce.get("sendMessageText").getContent();

            app.sendMessageButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                    status:"sendMessage", 
                    subject:app.sendMessageSubject,
                    text:app.sendMessageText,                                                                                                                                              
                })
                .then(function (response) {
                    //status=response.data.status;

                    if(response.data.mailResult.error_message != "")
                    {
                        app.emailMessageList = "<br>Email Send Error:<br>"
                        app.emailMessageList += response.data.mailResult.error_message + "<br><br>";
                    }
                    else
                    {
                        app.emailMessageList =  response.data.mailResult.mail_count + " messages sent.";                                     
                    }   

                    app.sendMessageButtonText = "Send Message <i class='fas fa-envelope fa-xs'></i>";                                                              
                    app.session.messageCount = response.data.messageCount;
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });
        },

         //send an email to all of the confirmed subjects
         reSendInvitation:function reSendInvitation(id){

            if(app.reSendMessageButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.reSendMessageButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                    status:"reSendInvitation", 
                    id:id,                                                                                                                                           
                })
                .then(function (response) {
                    
                    if(response.data.status == "success")
                    {

                        for(let i=0;i<app.invitationList.length;i++)
                        {
                            if(app.invitationList[i].id == id)
                            {
                                app.invitationList[i] = response.data.invitation;
                                app.formatInvitations();
                                break;
                            }
                        }
                    }

                    app.reSendMessageButtonText = "Re-send <i class='fas fa-envelope fa-xs'></i>";                                                              

                })
                .catch(function (error) {
                    console.log(error);
                                                                         
                });
        },

        //remove subject from a sesssion day
        removeSubject: function removeSubject(userId,esduId){

            if(confirm("Remove subject from session?")){
                
                document.getElementById("removeSubject" + esduId).innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
               
                axios.post('{{request.get_full_path}}', {
                    status:"removeSubject",   
                    userId:userId, 
                    esduId:esduId,   
                    actionAll:app.currentSessionDayActionAll,                                                                                                                     
                })
                .then(function (response) {
                    status=response.data.status;

                    app.session.experiment_session_days=response.data.es_min.experiment_session_days;   
                    app.currentSessionDay = Object.assign({},app.session.experiment_session_days[ app.currentSessionDayIndex]);

                    if(status=="success")
                    {
                        
                        // app.session.experiment_session_days = response.data.sessionDays.experiment_session_days;                                                                    
                    }
                    else
                    {
                        app.displayErrors(response.data.errors);
                    }                                   
                    
                })
                .catch(function (error) {
                    console.log(error);
                    //app.searching=false;                                                              
                });
            }                       
                                    
        },                  

        //change a subject's confirmation status
        confirmSubject: function confirmSubject(userId,esduId,confirmed){                       

            document.getElementById("confirmSubject" + esduId).innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
           
            axios.post('{{request.get_full_path}}', {
                status:"changeConfirmation",   
                userId:userId, 
                esduId:esduId,  
                confirmed:confirmed,          
                actionAll:app.currentSessionDayActionAll,                                                                                                         
            })
            .then(function (response) {
                status=response.data.status;

                app.session.experiment_session_days=response.data.es_min.experiment_session_days;   
                app.session.confirmedEmailList = response.data.es_min.confirmedEmailList;
                app.session.confirmedCount = response.data.es_min.confirmedCount;
                app.currentSessionDay = Object.assign({},app.session.experiment_session_days[ app.currentSessionDayIndex]);

                if(status=="success")
                {
                    
                    // app.session.experiment_session_days = response.data.sessionDays.experiment_session_days;                                                                    
                }
                else
                {
                    app.displayErrors(response.data.errors);
                }            

                app.updateDisplayLists();                       
                
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });                      
                                    
        },

        //search for a subject to add manually
        searchForSubject: function searchForSubject(){
            if(app.findButtonText != "Find") return;
            if(app.searchText == "") return;

            app.searchAddResult = "";

            app.findButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('{{request.get_full_path}}', {
                status:"searchForSubject",   
                searchInfo:app.searchText,                                                                                                                         
            })
            .then(function (response) {

                    
                app.findButtonText = 'Find';  
                status = response.data.status;

                if (status == "success")
                {
                    app.searchResults=JSON.parse(response.data.users);

                    if(app.searchResults.length > 0)
                    {
                        app.searchResultsEmptyText="";
                    }   
                    else
                    {
                        app.searchResultsEmptyText="No Users Found<br><br>";
                    } 
                }
                else
                {
                    app.searchResultsEmptyText=response.data.message + "<br><br>";
                }

                                                                    
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });                                       
                                
        },

        //clear search results
        clearSearchForSubject: function clearSearchForSubject(){

            app.searchResults=[];
            app.searchText="";  
            app.findButtonText="Find";                                    
        },

        //manually add subject to sessoin
        manuallyAddSubject: function manuallyAddSubject(u){

            document.getElementById("manualAdd" + u.id).innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"manuallyAddSubject",   
                user:u,
                sendInvitation:app.manualAddSendInvitation,                                                                                                                      
            })
            .then(function (response) {
                app.session.experiment_session_days=response.data.es_min.experiment_session_days;   

                app.searchResults=[];
                app.searchText="";   
                app.searchAddResult = "";

                status = response.data.status
                
                if(status != 'success')
                {
                    user = response.data.user;
                    
                    app.searchAddResult = 'Failed to add user to session: ';
                    app.searchAddResult += '<a href = "/userInfo/' + user.id + '" target="_blank" >'; 
                    app.searchAddResult += user.last_name + ", " + user.first_name + "</a><br>"
                                                                                    
                }
                else if(response.data.mailResult.error_message != "")
                {
                    app.searchAddResult += "<br>Email Send Error:<br>"
                    app.searchAddResult += response.data.mailResult.error_message + "<br><br>";
                }                            
                else if(response.data.mailResult.mail_count == 0)
                {
                    app.searchAddResult = "Subject added, no invitation was sent.";
                }
                else
                {                                               
                    app.searchAddResult = "Subject added, an invitation was sent.";                                 
                }      

                app.session.invitationCount = response.data.invitationCount;
                
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });                                       
                            
        },

        //show unconfirmed
        showUnconfirmedSubjects: function showUnconfirmedSubjects(u){

            app.showUnconfirmedButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"showUnconfirmedSubjects",   
                                                                                                                                            
            })
            .then(function (response) {
                app.session.experiment_session_days=response.data.es_min.experiment_session_days;                             
                app.currentSessionDay = Object.assign({},app.session.experiment_session_days[ app.currentSessionDayIndex]);

                app.showUnconfirmedButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });                                       
                            
            },

        //show message list
        showMessages:function showMessages(){

            app.showMessageListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"showMessages",                                                                                                    
            })
            .then(function (response) {
                app.messageList = response.data.messageList;     

                for(let i=0;i<app.messageList.length;i++)
                {
                    let m=app.messageList[i];
                    m.date_raw=app.formatDate(m.date_raw,false,false);

                    let emailMessageList="";

                    for(let j=0;j<m.users.length;j++)
                    {                                            
                            if (j >= 1)
                            {
                                if(j != m.users.length-1)
                                    emailMessageList += ", ";
                                else
                                    emailMessageList += " and "; 
                            }                                                                  

                            emailMessageList += '<a href = "/userInfo/' + m.users[j].id + '" target="_blank" >';
                            emailMessageList += m.users[j].first_name + " ";
                            emailMessageList += m.users[j].last_name; 
                            emailMessageList += "</a>";                                   
                    }

                    m.emailMessageList = emailMessageList;
                }                        
                
                app.showMessageListButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });
        },

        //show invitation list
        showInvitations:function showInvitations(){

            app.showInvitationListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"showInvitations",                                                                                                    
            })
            .then(function (response) {
                app.invitationList = response.data.invitationList;     

                app.formatInvitations();                                        
                
                app.showInvitationListButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });
        },
        
        //show invitation list
        downloadInvitations:function downloadInvitations(){

            app.downloadInvitationListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"downloadInvitations",                                                                                                    
            })
            .then(function (response) {             
                
                var downloadLink = document.createElement("a");
                var blob = new Blob(["\ufeff", response.data]);
                var url = URL.createObjectURL(blob);
                downloadLink.href = url;
                downloadLink.download = "Invited_Export_Session_" + app.session.id + ".csv";

                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
                app.downloadInvitationListButtonText = 'Download <i class="fas fa-download"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.searching=false;                                                              
            });
        },

        //format inivation messages for display
        formatInvitations:function formatInvitations(){
            for(let i=0;i<app.invitationList.length;i++)
            {
                let m=app.invitationList[i];
                m.date_raw=app.formatDate(m.date_raw,false,false);

                let emailMessageList="";

                for(let j=0;j<m.users.length;j++)
                {                                            
                        if (j >= 1)
                        {
                            if(j != m.users.length-1)
                                emailMessageList += ", ";
                            else
                                emailMessageList += " and "; 
                        }                                                                  

                        emailMessageList += '<a href = "/userInfo/' + m.users[j].id + '" target="_blank" >';
                        emailMessageList += m.users[j].first_name + " ";
                        emailMessageList += m.users[j].last_name; 
                        emailMessageList += "</a>";                                   
                }

                m.emailMessageList = emailMessageList;
            }
        },

        //fire when edit trait model needs to be shown
        showEditTraits:function showEditTraits(){                       
            app.editTraitsModal.show();
        },

        //fire when hide edit traits
        hideEditTraits:function hideEditTraits(){
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

        //fire when edit trait model needs to be shown
        showEditSession:function showEditSession(){         
            app.clearMainFormErrors();              
            app.cancelModal=true;
            app.sessionBeforeEdit = Object.assign({}, app.session);

            app.editSessionModal.show();
        },

        //fire when hide edit traits
        hideEditSession:function hideEditSession(){
            app.clearMainFormErrors();
            if(app.cancelModal)
            {
                Object.assign(app.session, app.sessionBeforeEdit);
                app.sessionBeforeEdit=null;
            }
        },

        //update require all trait constraints
        sendUpdateSession:function sendUpdateSession(){
            app.cancelModal=false;
            axios.post('{{request.get_full_path}}', {
                    status : "updateSession", 
                    formData : app.session,                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    if(response.data.status=="success")
                    {
                        app.session = response.data.session;                         
                        app.updateDisplayLists();   
                        app.editSessionModal.toggle();   
                    }
                    else
                    {
                        app.cancelModal=true;                           
                        app.displayErrors(response.data.errors);
                    }
         
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
        
        formatDate: function formatDate(value, date_only, show_timezone){
            if (value) {        
                //console.log(value);
                if(date_only)
                {
                    return moment(String(value)).local().format('MM/DD/YYYY');
                }
                else if(show_timezone)
                {
                    return moment(String(value)).local().format('MM/DD/YYYY hh:mm a ZZ');
                }
                else
                {
                    return moment(String(value)).local().format('MM/DD/YYYY hh:mm a');
                }
            }
            else{
                return "date format error";
            }
        },

        formatDateForInput: function formatDateForInput(value){
            if (value) {        
                return moment(String(value)).format('YYYY-MM-DDTHH:mm');
            }
            else{
                return "date format error";
            }
        },

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
        
        
    },

    //run when vue is mounted
    mounted(){
        Vue.nextTick(() => {
            this.getSession(); 
        });
    },                 

}).mount('#app');


