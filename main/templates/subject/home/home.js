axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{
        upcomingInvitations:[],
        pastAcceptedInvitations:[],
        allInvitations:[],
        showInvitationsText:'Show <i class="fa fa-eye fa-xs"></i>',
        noInvitationsFoundText:'',
        lastActionFailed:false,
        consentFormText:"",
        waiting:true,
        current_invitation:null,
        account_paused : {{account_paused|safe}},

        pixi_app:null,
        pixi_pointer_down:false,        
        pixi_signatures_rope_array:[],
        pixi_signature_texture:null,

        consent_form_error:"",
    },

    methods:{
        getCurrentInvitations:function(){
            
            axios.post('/subjectHome/', {
                            action :"getCurrentInvitations" ,                                                                                                                             
                        })
                        .then(function (response) {    
                            
                            app.takeUpcomingInvitations(response);
                            app.takePastAcceptedInvitations(response);
                            
                            app.$data.waiting=false;
                            
                            //test code
                            //app.viewConsentForm(app.$data.upcomingInvitations[0])
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },

        acceptConsentForm:function(){

            if(!app.$data.current_invitation) return;
            if(!app.$data.current_invitation.consent_form) return;

            app.$data.consent_form_error = "";

            consent_form_signature = {};
            consent_form_signature_resolution = {};

            if(app.$data.current_invitation.consent_form.signature_required)
            {
                if(app.$data.pixi_signatures_rope_array.length==0)
                {
                    app.$data.consent_form_error = "Sign before accepting.";
                    return;
                } 

                for(i=0;i<app.$data.pixi_signatures_rope_array.length;i++)
                {
                    consent_form_signature[i]=app.$data.pixi_signatures_rope_array[i].points;
                }

                let canvas = document.getElementById('signature_canvas_id');

                consent_form_signature_resolution['width']=canvas.width;;
                consent_form_signature_resolution['height']=canvas.height;
            }

            app.$data.waiting=true;

            axios.post('/subjectHome/', {
                            action :"acceptConsentForm",        
                            consent_form_id : app.$data.current_invitation.consent_form.id, 
                            consent_form_signature : consent_form_signature, 
                            consent_form_signature_resolution : consent_form_signature_resolution,                                                                                                                                                      
                        })
                        .then(function (response) {     
                            app.takeUpcomingInvitations(response);
                            app.takePastAcceptedInvitations(response);

                            if(app.$data.current_invitation)
                            {
                                let found = false;
                                for(let i=0;i<app.$data.upcomingInvitations.length;i++)
                                {
                                    if(app.$data.current_invitation.id == app.$data.upcomingInvitations[i].id)
                                    {
                                        app.$data.current_invitation = app.$data.upcomingInvitations[i];
                                        found=true;
                                        break;
                                    }
                                }

                                if(!found)
                                {
                                    for(let i=0;i<app.$data.pastAcceptedInvitations.length;i++)
                                    {
                                        if(app.$data.current_invitation.id == app.$data.pastAcceptedInvitations[i].id)
                                        {
                                            app.$data.current_invitation = app.$data.pastAcceptedInvitations[i];
                                            found=true
                                            break;
                                        }
                                    }
                                }

                                app.$data.waiting=false;
                            }
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        acceptInvitation:function(id,index){
            //$( '#acceptInvitation' + index ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');

            app.$data.upcomingInvitations[index].waiting=true;
            app.$data.waiting=true;

            axios.post('/subjectHome/', {
                            action :"acceptInvitation",
                            id:id,                                                                                                                             
                        })
                        .then(function (response) {     
                            app.takeUpcomingInvitations(response); 
                            app.$data.waiting=false;
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },

        cancelAcceptInvitation:function(id,index){
            //$( '#cancelAcceptInvitation' + index ).replaceWith('<i class="fas fa-spinner fa-spin"></i>');
            app.$data.upcomingInvitations[index].waiting=true;
            app.$data.waiting=true;

            axios.post('/subjectHome/', {
                            action :"cancelAcceptInvitation",
                            id:id,                                                                                                                             
                        })
                        .then(function (response) {     
                            app.takeUpcomingInvitations(response);  
                            app.$data.waiting=false;                                                                
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        showAllInvitations:function(index){
            app.$data.showInvitationsText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.$data.waiting=true;

            axios.post('/subjectHome/', {
                            action :"showAllInvitations",                                                                                                                            
                        })
                        .then(function (response) {     
                            app.$data.allInvitations=response.data.allInvitations;      
                            
                            app.$data.noInvitationsFoundText = "No invitations found"

                            for(var i=0;i<app.$data.allInvitations.length;i++)
                            {
                                app.$data.allInvitations[i].date = app.formatDate(app.$data.allInvitations[i].date,
                                                                                    null,
                                                                                    app.$data.allInvitations[i].enable_time,
                                                                                    null);                                       
                            }
                            
                            app.$data.showInvitationsText='Show <i class="fa fa-eye fa-xs"></i>';
                            app.$data.waiting=false;
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        takeUpcomingInvitations:function(response){            
             
            app.$data.upcomingInvitations=response.data.upcomingInvitations;                   

            for(var i=0;i<app.$data.upcomingInvitations.length;i++)
            {
                temp_s = app.$data.upcomingInvitations[i];

                for(var j=0;j<temp_s.experiment_session_days.length;j++)
                {
                    temp_s.experiment_session_days[j].date = app.formatDate(temp_s.experiment_session_days[j].date,
                                                                            temp_s.experiment_session_days[j].date_end,
                                                                            temp_s.experiment_session_days[j].enable_time,
                                                                            temp_s.experiment_session_days[j].length);
                }                        
            }
            
            app.$data.lastActionFailed = response.data.failed;
        },

        takePastAcceptedInvitations:function(response){
            app.$data.pastAcceptedInvitations=response.data.pastAcceptedInvitations;  
                        
            for(var i=0;i<app.$data.pastAcceptedInvitations.length;i++)
            {
                app.$data.pastAcceptedInvitations[i].date = app.formatDate(app.$data.pastAcceptedInvitations[i].date,
                                                                            null,
                                                                            app.$data.pastAcceptedInvitations[i].enable_time,
                                                                            null);

                app.$data.pastAcceptedInvitations[i].earnings = parseFloat(app.$data.pastAcceptedInvitations[i].earnings).toFixed(2);
                app.$data.pastAcceptedInvitations[i].total_earnings = parseFloat(app.$data.pastAcceptedInvitations[i].total_earnings).toFixed(2);
                app.$data.pastAcceptedInvitations[i].show_up_fee = parseFloat(app.$data.pastAcceptedInvitations[i].show_up_fee).toFixed(2);
            }
        },

        showInvitationText:function(index){
            $('#subject_consent_form_modal').modal('hide');
            app.$data.current_invitation = index;
            $('#subject_invitation_text_modal').modal('show');
        },

        viewConsentForm:function(invitation){   
            app.$data.current_invitation = invitation;

            $('#subject_invitation_text_modal').modal('hide');
            $('#subject_consent_form_modal').modal('show');

            //setTimeout(app.setupPixi, 500);
        },

        // updateConsentForm:function(invitation){
        //     app.$data.current_invitation = invitation;
        // },

        hideConsentForm:function(){           
            //$('#subject_consent_form_modal').modal('dispose');
        },

        handleResize:function(){
            if(app.$data.current_invitation)
            {
                
            }
            app.resetPixiApp();
        },

        formatDate: function(value,value2,enable_time,length){
                if (value) {        
                    //console.log(value);       
                    rValue =   moment(String(value)).local().format('dddd');
                    rValue +=   "<br>";
                    rValue +=   moment(String(value)).local().format('M/D/YYYY');   
                    rValue += "<br>";

                    if(enable_time)
                    {
                        rValue += moment(String(value)).local().format('h:mma'); 
                        if(value2 != null)
                        {
                            rValue += "-" + moment(String(value2)).local().format('h:mma'); 
                        }  
                    }
                    else
                    {
                        rValue += "Anytime";
                        
                        if(length != null)
                        {
                            rValue += ", " + length + " min";
                        }
                    }    
                    return rValue;
                }
                else{
                    return "date format error";
                }
        },

        checkMobile:function(){
            if( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ) {
                return true;
            }
            else
            {
                return false;
            }
        },

        {%include "subject/home/pixi_setup.js"%}
  
    },


    mounted: function(){
        this.getCurrentInvitations();        
        $('#subject_consent_form_modal').on("hidden.bs.modal", this.hideConsentForm);
        $('#subject_consent_form_modal').on("shown.bs.modal", this.handleResize);       

        window.addEventListener('resize', this.handleResize);     
    },
});

// pixi app