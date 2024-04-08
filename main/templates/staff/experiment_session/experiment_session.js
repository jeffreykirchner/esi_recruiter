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
            trait_id:0,
            min_value:0,
            max_vaue:0,
            include_if_in_range:true,
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
        options: {                                               //options for date time picker
            // https://momentjs.com/docs/#/displaying/
            format: 'MM/DD/YYYY hh:mm a ZZ',
            useCurrent: true,
            showClear: false,
            showClose: true,
            sideBySide: true,
            },   
        first_load : false,              //true after first load done   
        working : false,                   
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
            $(document).on('focusin', function(e) {
                if ($(e.target).closest(".tox-tinymce, .tox-tinymce-aux, .moxman-window, .tam-assetmanager-root").length) {
                    e.stopImmediatePropagation();
                }
            });

            $('#sessionModal').on("hidden.bs.modal", this.hideSetup);
            $('#editSessionModal').on("hidden.bs.modal", this.hideEditSession);
            $('#subjectsModalCenter').on("hidden.bs.modal", this.hideShowSubjects);
            $('#id_date').on("dp.hide",this.mainFormChange2);
            $('#inviteSubjectsModalCenter').on("hidden.bs.modal", this.hideInviteSubjects);
            $('#cancelSessionModalCenter').on("hidden.bs.modal", this.hideCancelSession);
            $('#manuallyAddSubjectsModalCenter').on("hidden.bs.modal", this.hideManuallyAddSubjects);
            $('#sendMessageModalCenter').on("hidden.bs.modal", this.hideSendMessage);
            $('#manuallyAddSubjectsModalCenter').on("hidden.bs.modal", this.hideEditInvitation);
            $('#editTraitsModal').on("hidden.bs.modal", this.hideEditTraits);
            $('#updateTraitModal').on("hidden.bs.modal", this.hideUpdateTrait);
        },    

        //remove all the form errors
        clearMainFormErrors:function clearMainFormErrors(){

            for(var item in app.$data.currentSessionDay)
            {
                $("#id_" + item).attr("class","form-control");
                $("#id_errors_" + item).remove();
            }

            for(var item in app.$data.session)
            {
                $("#id_" + item).attr("class","form-control");
                $("#id_errors_" + item).remove();
            }
        },

        //creates lists  of recruitment parameters
        updateDisplayLists:function updateDisplayLists(errors){
            var e = app.$data.recruitment_params;
            
            app.$data.include_institutions_list=app.updateDisplayLists2(e.institutions_include_full);
            app.$data.exclude_institutions_list=app.updateDisplayLists2(e.institutions_exclude_full);
            app.$data.include_experiments_list=app.updateDisplayLists2(e.experiments_include_full);
            app.$data.exclude_experiments_list=app.updateDisplayLists2(e.experiments_exclude_full);
            app.$data.include_schools_list=app.updateDisplayLists2(e.schools_include_full);
            app.$data.exclude_schools_list=app.updateDisplayLists2(e.schools_exclude_full);
            app.$data.trait_constraint_list=app.updateDisplayLists2(e.trait_constraints);
            app.$data.genders_list=app.updateDisplayLists2(e.gender_full);
            app.$data.subject_type_list=app.updateDisplayLists2(e.subject_type_full);
            
        },

        updateDisplayLists2:function updateDisplayLists2(list){
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

        //gets session info from the server
        getSession: function getSession(){
            axios.post('{{request.get_full_path}}', {
                    status:"get",                                                              
                })
                .then(function (response) {                                                                   
                    app.$data.session= response.data.session;
                    app.$data.experiment_invitation_text = response.data.experiment_invitation_text;
                    app.$data.recruitment_params = response.data.recruitment_params;                                
                    app.updateDisplayLists();
                    app.$data.showLoadingSpinner=false;
                    app.$data.invite_to_all = response.data.invite_to_all;

                    if(app.$data.session.canceled)
                    {
                        app.$data.cancelSessionButtonText = "*** CANCELED ***";
                    }

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

        //add a new session day
        addSessionDay: function addSessionDay(){
            if(app.$data.multiDayButtonText.includes("Multi"))
            {
                app.$data.multiDayButtonText = '<i class="fas fa-spinner fa-spin"></i>';

                axios.post('{{request.get_full_path}}', {
                    status:"addSessionDay", 
                    count:app.$data.multiDayCount,                                                             
                })
                .then(function (response) {                                   
                    app.$data.session= response.data.session;  
                    app.$data.session = response.data.session;             
                    
                    app.$data.multiDayButtonText = "Multi Day <i class='fas fa-plus fa-xs'></i>";
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
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
                        app.$data.session.experiment_session_days= response.data.sessionDays.experiment_session_days;                                
                        //app.updateDisplayLists();
                    })
                    .catch(function (error) {
                        console.log(error);
                        //app.$data.searching=false;                                                              
                    });                        
            }
        },

        //invite subjects
        inviteSubjects: function inviteSubjects(){
            if(!app.$data.inviteButtonText.includes("Invite")) return;

            app.$data.inviteButtonText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"inviteSubjects",     
                subjectInvitations:app.$data.subjectInvitations,                                                                
            })
            .then(function (response) {                                   

                status = response.data.status
                app.$data.session.experiment_session_days=response.data.es_min.experiment_session_days;
                
                app.$data.subjectInvitations = [];                    
                app.$data.subjectInvitationCount = 0;               
                app.$data.subjectInvitationList = ""; 

                if(status != 'success')
                {
                    userFails = response.data.userFails;

                    for (var i = 0; i < userFails.length; i++)
                    {
                        app.$data.subjectInvitationList += 'Failed to add user to session: ';
                        app.$data.subjectInvitationList += '<a href = "/userInfo/' + userFails[i].id + '" target="_blank" >'; 
                        app.$data.subjectInvitationList += userFails[i].last_name + ", " + userFails[i].first_name + "</a><br>"
                    }
                    
                    if(response.data.mailResult.error_message != "")
                    {
                        app.$data.subjectInvitationList += "<br>Email Send Error:<br>"
                        app.$data.subjectInvitationList += response.data.mailResult.error_message + "<br><br>";
                    }                                
                }                             
                else
                {      
                                                                
                    //$('#inviteSubjectsModalCenter').modal('toggle');                             
                }      
                app.$data.subjectInvitationList +=  response.data.mailResult.mail_count + " invitations sent.";  
                app.$data.inviteButtonText="";    
                app.$data.session.invitationCount = response.data.invitationCount;               
                
            })
            .catch(function (error) {
                console.log(error);                                                                                        
            }); 
        },

        //find subjects to invite
        findSubjectsToInvite: function findSubjectsToInvite(){

            if(app.$data.subjectInvitationList.includes('class')) return;

            app.$data.subjectInvitationList='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.$data.inviteResultsEmptyText="";

            axios.post('{{request.get_full_path}}', {
                status:"findSubjectsToInvite",    
                number:app.$data.subjectInvitationCount,                                                          
            })
            .then(function (response) {                                   
                app.$data.subjectInvitations = response.data.subjectInvitations;   
                
                var totalValid = response.data.totalValid;

                var s ="";
                var l = app.$data.subjectInvitations.length

                for (var i = 0; i < l; i++) {
                    if (l > 1)
                    {
                        if(i  > 0 && i != l-1)
                            s += ", ";
                        else if(i == l-1)
                            s += " and "; 
                    }                                                                  

                    s += '<a href = "/userInfo/' + app.$data.subjectInvitations[i].id + '" target="_blank" >';
                    s += app.$data.subjectInvitations[i].first_name + " ";
                    s += app.$data.subjectInvitations[i].last_name; 
                    s += "</a>";
                }

                s += "<br><br>";
                s += "<center><span style='color:gray;'>Total Found: " + totalValid + "<span><center>";

                app.$data.subjectInvitationList = s;  
                app.$data.inviteButtonText="Invite <i class='fa fa-users'></i>";    

                if(s=="") app.$data.inviteResultsEmptyText="No Users Found<br><br>";                       
                //app.updateDisplayLists();
            })
            .catch(function (error) {
                console.log(error);                                                                                        
            }); 
        },

        //clear subjects to invite
        clearSubjectsToInvite: function clearSubjectsToInvite(){
            app.$data.subjectInvitationList ="";
            app.$data.inviteButtonText="Invite <i class='fa fa-users'></i>";   
            app.$data.inviteResultsEmptyText="";                      
        },

        //cancel a session day (not in use)
        cancelSessionDay: function cancelSessionDay(){      
            if( app.$data.session.canceled) return;
            if(app.$data.subjectCancelationList=='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>') return;
            //if(app.$data.cancelSessionButtonText == "*** CANCELED ***" ) return;

            app.$data.subjectCancelationList='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('{{request.get_full_path}}', {
                    status:"cancelSession",   
                    //id:id,                                                           
                })
                .then(function (response) {                                   
                    app.$data.session = response.data.session;

                    app.$data.cancelSessionButtonText='*** CANCELED ***';

                    app.$data.subjectCancelationList = "";

                    if(response.data.mailResult.error_message != "")
                    {
                        app.$data.subjectCancelationList += "<br>Email Send Error:<br>"
                        app.$data.subjectCancelationList += response.data.mailResult.error_message + "<br><br>";
                    }
                    else
                    {
                        app.$data.subjectCancelationList +=  response.data.mailResult.mail_count + " cancelations sent.";                                     
                    }
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
                });                        
        },

        //update the session day parameters
        updateSessionDay: function updateSessionDay(){

            var sessionCanceledChangedMessage=false;

            if(app.$data.currentSessionDay.canceled != 
                app.$data.session.experiment_session_days[app.$data.currentSessionDayIndex].canceled)
            {
                if(confirm("Send email about cancellation update?")){
                    var sessionCanceledChangedMessage=true;
                }
            }

            var formData =  $("#mainForm2").serializeArray();

            //tz = moment.tz(formData[1].value)

            //formData[1].value = moment.tz(formData[1].value, tz ).utc().format();

            axios.post('{{request.get_full_path}}', {
                    status:"updateSessionDay",   
                    id:app.$data.currentSessionDay.id, 
                    formData : formData,
                    sessionCanceledChangedMessage:sessionCanceledChangedMessage,                                                          
                })
                .then(function (response) {
                    status=response.data.status;

                    app.clearMainFormErrors();

                    if(status=="success")
                    {
                        app.$data.session.experiment_session_days = response.data.sessionDays.experiment_session_days;                                
                        app.$data.cancelModal=false;
                        $('#sessionModal').modal('toggle');
                    }
                    else
                    {
                        app.displayErrors(response.data.errors);
                    }                                  
                    
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
                });                        
        },

        //update the session day parameters
        updateInvitationText: function updateInvitationText(){

            app.$data.updateInvitationButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.$data.session.invitationRawText = tinymce.get("id_invitationRawText").getContent();

            axios.post('{{request.get_full_path}}', {
                    status:"updateInvitationText",   
                    invitationRawText : app.$data.session.invitationRawText,                                                          
                })
                .then(function (response) {
                    app.$data.session.invitationText = response.data.invitationText;
                    
                    app.$data.updateInvitationButtonText ='Update <i class="fas fa-sign-in-alt"></i>';
                    $('#editInvitationTextModal').modal('toggle');
                
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
                });                        
        },

        //fill inviation text with experiment default
        fillInvitationWithDefault:function fillInvitationWithDefault(){
            app.$data.session.invitationRawText = app.$data.experiment_invitation_text;
            tinymce.get("id_invitationRawText").setContent(app.$data.session.invitationRawText);
        },

        //displays to the form errors
        displayErrors:function displayErrors(errors){
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
            }
        },

        //if form is changed add * to button
        recruitmentFormChange:function recruitmentFormChange(){
            app.$data.buttonText1="Update *";
        },

        //if form is changed add * to button
        mainFormChange2:function mainFormChange2(){
            app.$data.buttonText2="Update *";
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
            app.$data.addTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('{{request.get_full_path}}', {
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
        updateTrait:function updateTrait(){
            app.$data.updateTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('{{request.get_full_path}}', {
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
        deleteTrait:function deleteTrait(id){
            
            axios.post('{{request.get_full_path}}', {
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
        updateRequireAllTraitContraints:function updateRequireAllTraitContraints(){
            axios.post('{{request.get_full_path}}', {
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

        // fire when edit setup model is shown, save copy for cancel
        showSetup:function showSetup(id){
            app.$data.cancelModal=true;
            app.$data.currentSessionDay= Object.assign({},app.$data.session.experiment_session_days[id]);
            app.$data.currentSessionDayIndex=id;
            app.$data.currentSessionDay.date = app.formatDateForInput(app.$data.currentSessionDay.date_raw);
            app.$data.currentSessionDay.reminder_time = app.formatDateForInput(app.$data.currentSessionDay.reminder_time_raw);
            app.$data.sessionBeforeEdit = Object.assign({}, app.$data.session);
            app.$data.buttonText2="Update";
            $('#sessionModal').modal('show');
            //$('#id_date').datepicker('update');;
            app.clearMainFormErrors();
            //$('#id_date').val(app.formatDate(app.$data.currentSessionDay.date));
        },

        //fire when edit setup model hides, cancel action if nessicary
        hideSetup:function hideSetup(){
            if(app.$data.cancelModal)
            {
                Object.assign(app.$data.session, app.$data.sessionBeforeEdit);
                app.$data.sessionBeforeEdit=null;                            
                app.$data.buttonText2="Update";
            }
        },

        // fire when view subjects model is shown
        showSubjects:function showSubjects(id){
            app.$data.cancelModal=true;
            app.$data.currentSessionDay = Object.assign({},app.$data.session.experiment_session_days[id]);
            app.$data.currentSessionDayIndex =id;
            // app.$data.sessionBeforeEdit = Object.assign({}, app.$data.session);
            app.$data.buttonText3="Update";
            $('#subjectsModalCenter').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when view setup model closes, cancel action if nessicary
        hideShowSubjects:function hideShowSubjects(){    
            app.$data.showUnconfirmedButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';                    
        },

        // fire when invite subjects subjects model is shown
        showInviteSubjects:function showInviteSubjects(id){                        
            $('#inviteSubjectsModalCenter').modal('show');
            app.$data.inviteResultsEmptyText="";
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideInviteSubjects:function hideInviteSubjects(){   

            app.$data.subjectInvitations = [];                    
            app.$data.subjectInvitationCount = 0;               
            app.$data.subjectInvitationList = "";    
            
            app.$data.inviteButtonText="Invite <i class='fa fa-users'></i>";
        },

        // fire when cancel session model is shown
        showCancelSession:function showCancelSession(id){ 

            app.$data.subjectCancelationList = "";

            l="";
            s="Emails will be sent to the subjects that have confirmed: <br><br>"
            c1=app.$data.session.experiment_session_days.length;
            u1 = app.$data.session.confirmedEmailList

            for(i=0;i<u1.length;i++)
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

            app.$data.subjectCancelationList = s;
            $('#cancelSessionModalCenter').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when hide cancel session  model, cancel action if nessicary
        hideCancelSession:function hideCancelSession(){   

            
        },

        // fire when invite subjects subjects model is shown
        showEditInvitation:function showEditInvitation(id){    

            tinymce.get("id_invitationRawText").setContent(app.$data.session.invitationRawText);
            $('#editInvitationTextModal').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideEditInvitation:function hideEditInvitation(){       
                        
        },

        //invitation text changed, put * in buttonn text
        invitationTextChange:function invitationTextChange(){
            app.$data.updateInvitationButtonText="Update <i class='fas fa-sign-in-alt'></i> *";
        },

        // fire when invite subjects subjects model is shown
        showManuallyAddSubjects:function showManuallyAddSubjects(id){    
            app.$data.searchAddResult="";   
            app.$data.searchResults=[];
            app.$data.searchText=""; 
            app.$data.searchAddResult = "";          
            $('#manuallyAddSubjectsModalCenter').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideManuallyAddSubjects:function hideManuallyAddSubjects(){       
            app.$data.searchResults=[];
            app.$data.searchText="";  
            app.$data.findButtonText="Find";             
        },

        // fire when invite subjects subjects model is shown
        showSendMessage:function showSendMessage(id){    

            app.$data.emailMessageList="";
            tinymce.get("sendMessageText").setContent(app.sendMessageText);

            for(i=0;i<app.$data.session.confirmedEmailList.length;i++)
            {
                v = app.$data.session.confirmedEmailList[i];

                if(app.$data.emailMessageList != "")
                {
                    app.$data.emailMessageList += ", ";
                }
                
                app.$data.emailMessageList += '<a href = "/userInfo/' + v.user_id + '" target="_blank" >';
                app.$data.emailMessageList += v.user_email; 
                app.$data.emailMessageList += "</a>";
            }

            $('#sendMessageModalCenter').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideSendMessage:function hideSendMessage(){       
            app.$data.sendMessageText="<p>[first name],</p><p>If you have any questions contact [contact email].</p>";      
            app.$data.emailMessageList="";    
            // app.$data.sendMessageSubject=""; 
            app.$data.sendMessageButtonText = "Send Message <i class='fas fa-envelope fa-xs'></i>";       
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
                    subject:app.$data.sendMessageSubject,
                    text:app.$data.sendMessageText,                                                                                                                                              
                })
                .then(function (response) {
                    //status=response.data.status;

                    if(response.data.mailResult.error_message != "")
                    {
                        app.$data.emailMessageList = "<br>Email Send Error:<br>"
                        app.$data.emailMessageList += response.data.mailResult.error_message + "<br><br>";
                    }
                    else
                    {
                        app.$data.emailMessageList =  response.data.mailResult.mail_count + " messages sent.";                                     
                    }   

                    app.$data.sendMessageButtonText = "Send Message <i class='fas fa-envelope fa-xs'></i>";                                                              
                    app.$data.session.messageCount = response.data.messageCount;
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
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

                        for(i=0;i<app.invitationList.length;i++)
                        {
                            if(app.invitationList[i].id == id)
                            {
                                app.invitationList[i] = response.data.invitation;
                                app.formatInvitations();
                                break;
                            }
                        }
                    }

                    app.$data.reSendMessageButtonText = "Re-send <i class='fas fa-envelope fa-xs'></i>";                                                              

                })
                .catch(function (error) {
                    console.log(error);
                                                                         
                });
        },

        //remove subject from a sesssion day
        removeSubject: function removeSubject(userId,esduId){

            if(confirm("Remove subject from session?")){

                $( '#removeSubject' + esduId ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');

                axios.post('{{request.get_full_path}}', {
                    status:"removeSubject",   
                    userId:userId, 
                    esduId:esduId,   
                    actionAll:app.$data.currentSessionDayActionAll,                                                                                                                     
                })
                .then(function (response) {
                    status=response.data.status;

                    app.$data.session.experiment_session_days=response.data.es_min.experiment_session_days;   
                    app.$data.currentSessionDay = Object.assign({},app.$data.session.experiment_session_days[ app.$data.currentSessionDayIndex]);

                    if(status=="success")
                    {
                        
                        // app.$data.session.experiment_session_days = response.data.sessionDays.experiment_session_days;                                                                    
                    }
                    else
                    {
                        app.displayErrors(response.data.errors);
                    }                                   
                    
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
                });
            }                       
                                    
        },                  

        //change a subject's confirmation status
        confirmSubject: function confirmSubject(userId,esduId,confirmed){                       

            $( '#confirmSubject' + esduId ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');

            axios.post('{{request.get_full_path}}', {
                status:"changeConfirmation",   
                userId:userId, 
                esduId:esduId,  
                confirmed:confirmed,          
                actionAll:app.$data.currentSessionDayActionAll,                                                                                                         
            })
            .then(function (response) {
                status=response.data.status;

                app.$data.session.experiment_session_days=response.data.es_min.experiment_session_days;   
                app.$data.session.confirmedEmailList = response.data.es_min.confirmedEmailList;
                app.$data.session.confirmedCount = response.data.es_min.confirmedCount;
                app.$data.currentSessionDay = Object.assign({},app.$data.session.experiment_session_days[ app.$data.currentSessionDayIndex]);

                if(status=="success")
                {
                    
                    // app.$data.session.experiment_session_days = response.data.sessionDays.experiment_session_days;                                                                    
                }
                else
                {
                    app.displayErrors(response.data.errors);
                }            

                app.updateDisplayLists();                       
                
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });                      
                                    
        },

        //search for a subject to add manually
        searchForSubject: function searchForSubject(){
            if(app.$data.findButtonText != "Find") return;
            if(app.$data.searchText == "") return;

            app.$data.searchAddResult = "";

            app.$data.findButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('{{request.get_full_path}}', {
                status:"searchForSubject",   
                searchInfo:app.$data.searchText,                                                                                                                         
            })
            .then(function (response) {

                    
                app.$data.findButtonText = 'Find';  
                status = response.data.status;

                if (status == "success")
                {
                    app.$data.searchResults=JSON.parse(response.data.users);

                    if(app.$data.searchResults.length > 0)
                    {
                        app.$data.searchResultsEmptyText="";
                    }   
                    else
                    {
                        app.$data.searchResultsEmptyText="No Users Found<br><br>";
                    } 
                }
                else
                {
                    app.$data.searchResultsEmptyText=response.data.message + "<br><br>";
                }

                                                                    
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });                                       
                                
        },

        //clear search results
        clearSearchForSubject: function clearSearchForSubject(){

            app.$data.searchResults=[];
            app.$data.searchText="";  
            app.$data.findButtonText="Find";                                    
        },

        //manually add subject to sessoin
        manuallyAddSubject: function manuallyAddSubject(u){

            $( '#manualAdd' + u.id ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');

            axios.post('{{request.get_full_path}}', {
                status:"manuallyAddSubject",   
                user:u,
                sendInvitation:app.$data.manualAddSendInvitation,                                                                                                                      
            })
            .then(function (response) {
                app.$data.session.experiment_session_days=response.data.es_min.experiment_session_days;   
                //$('#manuallyAddSubjectsModalCenter').modal('toggle');
                app.$data.searchResults=[];
                app.$data.searchText="";   
                app.$data.searchAddResult = "";

                status = response.data.status
                
                if(status != 'success')
                {
                    user = response.data.user;
                    
                    app.$data.searchAddResult = 'Failed to add user to session: ';
                    app.$data.searchAddResult += '<a href = "/userInfo/' + user.id + '" target="_blank" >'; 
                    app.$data.searchAddResult += user.last_name + ", " + user.first_name + "</a><br>"
                                                                                    
                }
                else if(response.data.mailResult.error_message != "")
                {
                    app.$data.searchAddResult += "<br>Email Send Error:<br>"
                    app.$data.searchAddResult += response.data.mailResult.error_message + "<br><br>";
                }                            
                else if(response.data.mailResult.mail_count == 0)
                {
                    app.$data.searchAddResult = "Subject added, no invitation was sent.";
                }
                else
                {                                               
                    app.$data.searchAddResult = "Subject added, an invitation was sent.";                                 
                }      

                app.$data.session.invitationCount = response.data.invitationCount;
                
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });                                       
                            
        },

        //show unconfirmed
        showUnconfirmedSubjects: function showUnconfirmedSubjects(u){

            app.$data.showUnconfirmedButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"showUnconfirmedSubjects",   
                                                                                                                                            
            })
            .then(function (response) {
                app.$data.session.experiment_session_days=response.data.es_min.experiment_session_days;                             
                app.$data.currentSessionDay = Object.assign({},app.$data.session.experiment_session_days[ app.$data.currentSessionDayIndex]);

                app.$data.showUnconfirmedButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });                                       
                            
            },

        //show message list
        showMessages:function showMessages(){

            app.$data.showMessageListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"showMessages",                                                                                                    
            })
            .then(function (response) {
                app.$data.messageList = response.data.messageList;     

                for(i=0;i<app.$data.messageList.length;i++)
                {
                    m=app.$data.messageList[i];
                    m.date_raw=app.formatDate(m.date_raw,false,false);

                    emailMessageList="";

                    for(j=0;j<m.users.length;j++)
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
                
                app.$data.showMessageListButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });
        },

        //show invitation list
        showInvitations:function showInvitations(){

            app.$data.showInvitationListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"showInvitations",                                                                                                    
            })
            .then(function (response) {
                app.$data.invitationList = response.data.invitationList;     

                app.formatInvitations();                                        
                
                app.$data.showInvitationListButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });
        },
        
        //show invitation list
        downloadInvitations:function downloadInvitations(){

            app.$data.downloadInvitationListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('{{request.get_full_path}}', {
                status:"downloadInvitations",                                                                                                    
            })
            .then(function (response) {             
                
                var downloadLink = document.createElement("a");
                var blob = new Blob(["\ufeff", response.data]);
                var url = URL.createObjectURL(blob);
                downloadLink.href = url;
                downloadLink.download = "Invited_Export_Session_" + app.$data.session.id + ".csv";

                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
                app.$data.downloadInvitationListButtonText = 'Download <i class="fas fa-download"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });
        },

        //format inivation messages for display
        formatInvitations:function formatInvitations(){
            for(i=0;i<app.$data.invitationList.length;i++)
            {
                m=app.$data.invitationList[i];
                m.date_raw=app.formatDate(m.date_raw,false,false);

                emailMessageList="";

                for(j=0;j<m.users.length;j++)
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
            $('#editTraitsModal').modal('show');
        },

        //fire when hide edit traits
        hideEditTraits:function hideEditTraits(){
        },

        // fire when edit trait model is shown
        showUpdateTrait:function showUpdateTrait(id,index){

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
        hideUpdateTrait:function hideUpdateTrait(){
            if(app.$data.cancelModal)
            {
            
            }
        },

        //fire when edit trait model needs to be shown
        showEditSession:function showEditSession(){         
            app.clearMainFormErrors();              
            app.$data.cancelModal=true;
            app.$data.sessionBeforeEdit = Object.assign({}, app.$data.session);

            $('#editSessionModal').modal('show');
        },

        //fire when hide edit traits
        hideEditSession:function hideEditSession(){
            app.clearMainFormErrors();
            if(app.$data.cancelModal)
            {
                Object.assign(app.$data.session, app.$data.sessionBeforeEdit);
                app.$data.sessionBeforeEdit=null;
            }
        },

        //update require all trait constraints
        sendUpdateSession:function sendUpdateSession(){
            app.$data.cancelModal=false;
            axios.post('{{request.get_full_path}}', {
                    status : "updateSession", 
                    formData : $("#mainForm1").serializeArray(),                                                                                                                                                             
                })
                .then(function (response) {                                   
                    
                    if(response.data.status=="success")
                    {
                        app.$data.session = response.data.session;  
                        app.updateDisplayLists();   
                        $('#editSessionModal').modal('toggle');   
                    }
                    else
                    {
                        app.$data.cancelModal=true;                           
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
           
            $('#editAllowListModal').modal('show');
        },

        //update require all trait constraints
        sendAddToAllowList:function sendAddToAllowList(){

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

        sendClearAllowList:function sendClearAllowList(){

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
       
        //attach modal close events to vue
        //$('#recruitmentModalCenter').on("hidden.bs.modal", this.hideEditRecruitment);
        
        this.getSession();
        
    },                 

}).mount('#app');

// // http://eonasdan.github.io/bootstrap-datetimepicker/
// app.component('date-picker', VueBootstrapDatetimePicker);

// $.extend(true, $.fn.datetimepicker.defaults, {
//     icons: {
//         time: 'far fa-clock',
//         date: 'far fa-calendar',
//         up: 'fas fa-arrow-up',
//         down: 'fas fa-arrow-down',
//         previous: 'fas fa-chevron-start',
//         next: 'fas fa-chevron-end',
//         today: 'fas fa-calendar-check',
//         clear: 'far fa-trash-alt',
//         close: 'far fa-times-circle'
//     }
//     });


