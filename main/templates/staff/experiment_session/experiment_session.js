axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

// http://eonasdan.github.io/bootstrap-datetimepicker/
Vue.component('date-picker', VueBootstrapDatetimePicker);

$.extend(true, $.fn.datetimepicker.defaults, {
    icons: {
        time: 'far fa-clock',
        date: 'far fa-calendar',
        up: 'fas fa-arrow-up',
        down: 'fas fa-arrow-down',
        previous: 'fas fa-chevron-left',
        next: 'fas fa-chevron-right',
        today: 'fas fa-calendar-check',
        clear: 'far fa-trash-alt',
        close: 'far fa-times-circle'
    }
    });

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{        
        sessionURL:'',   
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
        sendMessageText:"[first name],\n\nIf you have any questions contact [contact email].",   //text of send message     
        emailMessageList:"",                 //emails for send message    
        sendMessageButtonText:"Send Message <i class='fas fa-envelope fa-xs'></i>", 
        session:{
                    invitationText:"",                         //invitation text with variables filled in 
                    experiment_session_days:[],                //days in session
                    invitationRawText:"",                      //invitation text with editable variables             
                    messageCount:"",                           //number of email messages sent out
                    invitationCount:"",                        //number of invition groups sent out
                    allowDelete:false,                         //allow session to be deleted or canceled
                    confirmedCount:0,                          //number of subjects that have confirmed to be in session
                    confirmedEmailList:[]},                    //list of emails that
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
        currentSessionDay:{ account:0,                              //session active in modal
                            actual_participants:0,
                            auto_reminder:true,
                            enable_time:true,
                            canceled:0,
                            date_raw:"",
                            date:"",
                            date_local:"",
                            reminder_time_raw:"",
                            reminder_time:"",
                            reminder_time_local:"",
                            custom_reminder_time:false,
                            account:0,
                            id:0,
                            length:0,
                            location:0,
                            registration_cutoff:0,
                            experiment_session_days_user:[],
                            experiment_session_days_user_unconfirmed:[],
                            confirmedCount:"-",
                            unConfirmedCount:"-"},       
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
        options: {                                               //options for date time picker
            // https://momentjs.com/docs/#/displaying/
            format: 'MM/DD/YYYY hh:mm a ZZ',
            useCurrent: true,
            showClear: false,
            showClose: true,
            sideBySide: true,
            },                         
    },

    methods:{     

        //remove all the form errors
        clearMainFormErrors:function(){

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

        //update recruitment parameters 
        updateRecruitmentParameters: function(){                       
            axios.post('/experimentSession/{{id}}/', {
                    status :"updateRecruitmentParameters" ,                                
                    formData : $("#updateRecruitmentParametersForm").serializeArray(),                                                              
                })
                .then(function (response) {     
                                                
                    status=response.data.status;                               

                    app.clearMainFormErrors();

                    if(status=="success")
                    {                                 
                        app.$data.recruitment_params= response.data.recruitment_params;  
                        app.updateDisplayLists();

                        app.$data.cancelModal=false; 
                        $('#recruitmentModalCenter').modal('toggle');
                    }
                    else
                    {                                
                        app.displayErrors(response.data.errors);
                    }          

                    app.$data.buttonText1="Update"                      
                })
                .catch(function (error) {
                    console.log(error);
                    app.$data.searching=false;
                });                        
            },

        //creates lists  of recruitment parameters
        updateDisplayLists:function(errors){
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

        //gets session info from the server
        getSession: function(){
            axios.post('/experimentSession/{{id}}/', {
                    status:"get",                                                              
                })
                .then(function (response) {                                                                   
                    app.$data.session= response.data.session;
                    app.$data.experiment_invitation_text = response.data.experiment_invitation_text;
                    app.$data.recruitment_params= response.data.recruitment_params;                                
                    app.updateDisplayLists();
                    app.$data.showLoadingSpinner=false;

                    if(app.$data.session.canceled)
                    {
                        app.$data.cancelSessionButtonText = "*** CANCELED ***";
                    }
                })
                .catch(function (error) {
                    console.log(error);
                    //app.$data.searching=false;                                                              
                });                        
        },

        //add a new session day
        addSessionDay: function(){
            if(app.$data.multiDayButtonText.includes("Multi"))
            {
                app.$data.multiDayButtonText = '<i class="fas fa-spinner fa-spin"></i>';

                axios.post('/experimentSession/{{id}}/', {
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
        removeSessionDay: function(id){
            if(confirm("Delete Session Day?")){
                axios.post('/experimentSession/{{id}}/', {
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
        inviteSubjects: function(){
            if(!app.$data.inviteButtonText.includes("Invite")) return;

            app.$data.inviteButtonText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('/experimentSession/{{id}}/', {
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
        findSubjectsToInvite: function(){

            if(app.$data.subjectInvitationList.includes('class')) return;

            app.$data.subjectInvitationList='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.$data.inviteResultsEmptyText="";

            axios.post('/experimentSession/{{id}}/', {
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
        clearSubjectsToInvite: function(){
            app.$data.subjectInvitationList ="";
            app.$data.inviteButtonText="Invite <i class='fa fa-users'></i>";   
            app.$data.inviteResultsEmptyText="";                      
        },

        //cancel a session day (not in use)
        cancelSessionDay: function(){      
            if( app.$data.session.canceled) return;
            if(app.$data.subjectCancelationList=='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>') return;
            //if(app.$data.cancelSessionButtonText == "*** CANCELED ***" ) return;

            app.$data.subjectCancelationList='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';

            axios.post('/experimentSession/{{id}}/', {
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
        updateSessionDay: function(){

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

            axios.post('/experimentSession/{{id}}/', {
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
                        $('#setupModalCenter').modal('toggle');
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
        updateInvitationText: function(){

            app.$data.updateInvitationButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSession/{{id}}/', {
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
        fillInvitationWithDefault:function(){
            app.$data.session.invitationRawText = app.$data.experiment_invitation_text;
        },

        //displays to the form errors
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
            }
        },

        //if form is changed add * to button
        recruitmentFormChange:function(){
            app.$data.buttonText1="Update *";
        },

        //if form is changed add * to button
        mainFormChange2:function(){
            app.$data.buttonText2="Update *";
        },

        // fire when edit experiment model is shown, save copy for cancel
        showEditRecruitment:function(){
            // app.$data.cancelModal=true;
            // app.$data.sessionBeforeEdit = Object.assign({}, app.$data.session);
            // app.$data.recruitment_paramsBeforeEdit = Object.assign({}, app.$data.recruitment_params);
            // $('#recruitmentModalCenter').modal('show');
            // app.clearMainFormErrors();

            window.open("{%url 'experimentSessionParametersView' session.id %}","_self");
        },

        //fire when edit experiment model hides, cancel action if nessicary
        hideEditRecruitment:function(){
            if(app.$data.cancelModal)
            {
                Object.assign(app.$data.session, app.$data.sessionBeforeEdit);
                Object.assign(app.$data.recruitment_params, app.$data.recruitment_paramsBeforeEdit);
                app.$data.sessionBeforeEdit=null;
                app.$data.buttonText1="Update";
            }
        },

        //fire when the run session button is pressed
        runSession:function(id)
        {
            window.open('/experimentSessionRun/' + id,"_self");
        },

        //add trait
        addTrait:function(){
            app.$data.addTraitButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experimentSession/{{id}}/', {
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
            axios.post('/experimentSession/{{id}}/', {
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
            
            axios.post('/experimentSession/{{id}}/', {
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
            axios.post('/experimentSession/{{id}}/', {
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
        showSetup:function(id){
            app.$data.cancelModal=true;
            app.$data.currentSessionDay= Object.assign({},app.$data.session.experiment_session_days[id]);
            app.$data.currentSessionDayIndex=id;
            app.$data.currentSessionDay.date_local = app.formatDate(app.$data.currentSessionDay.date_raw,false,true);
            app.$data.currentSessionDay.reminder_time_local = app.formatDate(app.$data.currentSessionDay.reminder_time_raw,false,true);
            app.$data.sessionBeforeEdit = Object.assign({}, app.$data.session);
            app.$data.buttonText2="Update";
            $('#setupModalCenter').modal('show');
            //$('#id_date').datepicker('update');;
            app.clearMainFormErrors();
            //$('#id_date').val(app.formatDate(app.$data.currentSessionDay.date));
        },

        //fire when edit setup model hides, cancel action if nessicary
        hideSetup:function(){
            if(app.$data.cancelModal)
            {
                Object.assign(app.$data.session, app.$data.sessionBeforeEdit);
                app.$data.sessionBeforeEdit=null;                            
                app.$data.buttonText2="Update";
            }
        },

        // fire when view subjects model is shown
        showSubjects:function(id){
            app.$data.cancelModal=true;
            app.$data.currentSessionDay = Object.assign({},app.$data.session.experiment_session_days[id]);
            app.$data.currentSessionDayIndex =id;
            // app.$data.sessionBeforeEdit = Object.assign({}, app.$data.session);
            app.$data.buttonText3="Update";
            $('#subjectsModalCenter').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when view setup model closes, cancel action if nessicary
        hideShowSubjects:function(){    
            app.$data.showUnconfirmedButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';                    
        },

        // fire when invite subjects subjects model is shown
        showInviteSubjects:function(id){                        
            $('#inviteSubjectsModalCenter').modal('show');
            app.$data.inviteResultsEmptyText="";
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideInviteSubjects:function(){   

            app.$data.subjectInvitations = [];                    
            app.$data.subjectInvitationCount = 0;               
            app.$data.subjectInvitationList = "";    
            
            app.$data.inviteButtonText="Invite <i class='fa fa-users'></i>";
        },

        // fire when cancel session model is shown
        showCancelSession:function(id){ 

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
        hideCancelSession:function(){   

            
        },

        // fire when invite subjects subjects model is shown
        showEditInvitation:function(id){    
            $('#editInvitationTextModal').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideEditInvitation:function(){       
                        
        },

        //invitation text changed, put * in buttonn text
        invitationTextChange:function(){
            app.$data.updateInvitationButtonText="Update <i class='fas fa-sign-in-alt'></i> *";
        },

        // fire when invite subjects subjects model is shown
        showManuallyAddSubjects:function(id){    
            app.$data.searchAddResult="";   
            app.$data.searchResults=[];
            app.$data.searchText=""; 
            app.$data.searchAddResult = "";          
            $('#manuallyAddSubjectsModalCenter').modal('show');
            // app.clearMainFormErrors();
        },

        //fire when hide invite subjects  model, cancel action if nessicary
        hideManuallyAddSubjects:function(){       
            app.$data.searchResults=[];
            app.$data.searchText="";  
            app.$data.findButtonText="Find";             
        },

        // fire when invite subjects subjects model is shown
        showSendMessage:function(id){    

            app.$data.emailMessageList="";

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
        hideSendMessage:function(){       
            app.$data.sendMessageText="";      
            app.$data.emailMessageList="";    
            app.$data.sendMessageSubject=""; 
            app.$data.sendMessageButtonText = "Send Message <i class='fas fa-envelope fa-xs'></i>";       
        },

        //send an email to all of the confirmed subjects
        sendEmailMessage:function(){

            if(app.$data.sendMessageSubject == "" )
            {
                confirm("Add a subject to your message.");
                return;
            }

            if(app.$data.sendMessageText == "" )
            {
                confirm("Your message is empty.");
                return;
            }

            if(app.$data.sendMessageButtonText == '<i class="fas fa-spinner fa-spin"></i>') return;

            app.$data.sendMessageButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSession/{{id}}/', {
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

        //remove subject from a sesssion day
        removeSubject: function(userId,esduId){

            if(confirm("Remove subject from session?")){

                $( '#removeSubject' + esduId ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');

                axios.post('/experimentSession/{{id}}/', {
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
        confirmSubject: function(userId,esduId,confirmed){                       

            $( '#confirmSubject' + esduId ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');

            axios.post('/experimentSession/{{id}}/', {
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
        searchForSubject: function(){
            if(app.$data.findButtonText != "Find") return;
            if(app.$data.searchText == "") return;

            app.$data.searchAddResult = "";

            app.$data.findButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            axios.post('/experimentSession/{{id}}/', {
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
        clearSearchForSubject: function(){

            app.$data.searchResults=[];
            app.$data.searchText="";  
            app.$data.findButtonText="Find";                                    
        },

        //manually add subject to sessoin
        manuallyAddSubject: function(u){

            $( '#manualAdd' + u.id ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');

            axios.post('/experimentSession/{{id}}/', {
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
        showUnconfirmedSubjects: function(u){

            app.$data.showUnconfirmedButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSession/{{id}}/', {
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
        showMessages:function(){

            app.$data.showMessageListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSession/{{id}}/', {
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
        showInvitations:function(){

            app.$data.showInvitationListButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSession/{{id}}/', {
                status:"showInvitations",                                                                                                    
            })
            .then(function (response) {
                app.$data.invitationList = response.data.invitationList;     

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
                
                app.$data.showInvitationListButtonText = 'Show <i class="fa fa-eye fa-xs"></i>';
            })
            .catch(function (error) {
                console.log(error);
                //app.$data.searching=false;                                                              
            });
            },

        //fire when edit trait model needs to be shown
        showEditTraits:function(){                       
            $('#editTraitsModal').modal('show');
        },

        //fire when hide edit traits
        hideEditTraits:function(){
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
        
        formatDate: function(value,date_only,show_timezone){
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
        
        
    },

    //run when vue is mounted
    mounted: function(){
        this.getSession();
        //attach modal close events to vue
        $('#recruitmentModalCenter').on("hidden.bs.modal", this.hideEditRecruitment);
        $('#setupModalCenter').on("hidden.bs.modal", this.hideSetup);
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

});


