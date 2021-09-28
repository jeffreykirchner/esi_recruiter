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
        consent_required:false,
        consentFormText:"",
        waiting:true,
        current_invitation_text:"",
    },

    methods:{
        getCurrentInvitations:function(){
            
            axios.post('/subjectHome/', {
                            action :"getCurrentInvitations" ,                                                                                                                             
                        })
                        .then(function (response) {    
                            
                            app.takeUpcomingInvitations(response);
                            app.$data.consentFormText = response.data.consentFormText;
                            
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

                            app.$data.waiting=false;
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },

        acceptConsentForm:function(){

            axios.post('/subjectHome/', {
                            action :"acceptConsentForm",                                                                                                                                                                
                        })
                        .then(function (response) {     
                            app.takeUpcomingInvitations(response);                                                                     
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
            
            app.$data.consent_required=response.data.consent_required; 
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

            if(app.$data.consent_required)
            {
                $('#consentModal').modal({backdrop: 'static', keyboard: false}).show();
            }
            else
            {
                if(($("#consentModal").data('bs.modal') || {})._isShown)
                {
                    $('#consentModal').modal('toggle');
                }                        
            }
        },

        showInvitationText:function(index){
            app.$data.current_invitation_text = app.$data.upcomingInvitations[index].invitation_text;
            $('#subject_invitation_text_modal').modal('toggle');
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
    },

    mounted: function(){
        this.getCurrentInvitations();                    
    },
});