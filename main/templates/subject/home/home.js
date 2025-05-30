"use strict";
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

let app = Vue.createApp({

    delimiters: ['[[', ']]'],
  
    data() {return{
        upcomingInvitations:[],
        pastAcceptedInvitations:[],
        umbrellaConsents:[],
        requiredUmbrellaConsents:[],
        allInvitations:[],
        showInvitationsText:'Show <i class="fa fa-eye fa-xs"></i>',
        noInvitationsFoundText:'',
        lastActionFailed:false,
        consentFormText:"",
        waiting:true,
        current_invitation:null,
        account_paused : {{account_paused|safe}},

        //modals
        subject_consent_form_modal:null,

    }},

    methods:{
        getCurrentInvitations:function getCurrentInvitations(){
            
            axios.post('/subjectHome/', {
                            action :"getCurrentInvitations" ,                                                                                                                             
                        })
                        .then(function (response) {    
                            
                            app.takeUpcomingInvitations(response);
                            app.takePastAcceptedInvitations(response);

                            app.umbrellaConsents = response.data.umbrellaConsents;
                            app.requiredUmbrellaConsents = response.data.requiredUmbrellaConsents;
                            
                            app.waiting=false;
                            
                            if(app.requiredUmbrellaConsents.length>0)
                            {
                              app.subject_consent_form_modal.toggle();
                            }

                            //test code
                            //app.viewConsentForm(app.upcomingInvitations[0])
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        acceptInvitation:function acceptInvitation(id,index){

            app.upcomingInvitations[index].waiting=true;
            app.waiting=true;

            axios.post('/subjectHome/', {
                            action :"acceptInvitation",
                            id:id,                                                                                                                             
                        })
                        .then(function (response) {     
                            app.takeUpcomingInvitations(response); 
                            app.waiting=false;
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },

        cancelAcceptInvitation:function cancelAcceptInvitation(id,index){

            app.upcomingInvitations[index].waiting=true;
            app.waiting=true;

            axios.post('/subjectHome/', {
                            action :"cancelAcceptInvitation",
                            id:id,                                                                                                                             
                        })
                        .then(function (response) {     
                            app.takeUpcomingInvitations(response);  
                            app.waiting=false;                                                                
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        showAllInvitations:function showAllInvitations(index){
            app.showInvitationsText='<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>';
            app.waiting=true;

            axios.post('/subjectHome/', {
                            action :"showAllInvitations",                                                                                                                            
                        })
                        .then(function (response) {     
                            app.allInvitations=response.data.allInvitations;      
                            
                            app.noInvitationsFoundText = "No invitations found"

                            for(let i=0;i<app.allInvitations.length;i++)
                            {
                                app.allInvitations[i].date = app.formatDate(app.allInvitations[i].date,
                                                                                    null,
                                                                                    app.allInvitations[i].enable_time,
                                                                                    null);                                       
                            }
                            
                            app.showInvitationsText='Show <i class="fa fa-eye fa-xs"></i>';
                            app.waiting=false;

                            let result = "";

                            for(let i=0;i<app.allInvitations.length;i++)
                            {
                                let s = app.allInvitations[i];

                                result += `
                                    <tr>
                                        <td  class="text-center">                                                                
                                            ${s.date_html}
                                            ${s.multiDay ? '<div>(Multi-day)</div>' : ''}                                 
                                        </td>
                                        <td class="text-center">`
                                
                                if(s.noShow)
                                    result += `<div class="text-danger">No Show</div>`;
                                else if(s.canceled)
                                    result += `<div class="text-danger">Canceled</div>`;
                                else if(s.bumped)
                                    result += `<div>Bumped</div>`;
                                else if(s.attended)
                                    result += `<div>Attended</div>`;
                                else if(s.confirmed)
                                    result += `<div>Confirmed</div>`;                                                                                             
                            
                                result += `
                                        </td>
                                    </tr>
                                `;
                            }
                            
                            let id_all_anvitations = document.getElementById("allInvitations");
                            id_all_anvitations.innerHTML = result;
                        })
                        .catch(function (error) {
                            console.log(error);                                    
                        });                        
        },
        
        takeUpcomingInvitations:function takeUpcomingInvitations(response){            
             
            app.upcomingInvitations=response.data.upcomingInvitations;                   

            for(let i=0;i<app.upcomingInvitations.length;i++)
            {
                let temp_s = app.upcomingInvitations[i];

                // for(let j=0;j<temp_s.experiment_session_days.length;j++)
                // {
                //     temp_s.experiment_session_days[j].date = app.formatDate(temp_s.experiment_session_days[j].date,
                //                                                             temp_s.experiment_session_days[j].date_end,
                //                                                             temp_s.experiment_session_days[j].enable_time,
                //                                                             temp_s.experiment_session_days[j].length);
                // }                        
            }
            
            app.lastActionFailed = response.data.failed;
        },

        takePastAcceptedInvitations:function takePastAcceptedInvitations(response){
            app.pastAcceptedInvitations=response.data.pastAcceptedInvitations;  
                        
            for(let i=0;i<app.pastAcceptedInvitations.length;i++)
            {
                app.pastAcceptedInvitations[i].date = app.formatDate(app.pastAcceptedInvitations[i].date,
                                                                            null,
                                                                            app.pastAcceptedInvitations[i].enable_time,
                                                                            null);

                app.pastAcceptedInvitations[i].earnings = parseFloat(app.pastAcceptedInvitations[i].earnings).toFixed(2);
                app.pastAcceptedInvitations[i].total_earnings = parseFloat(app.pastAcceptedInvitations[i].total_earnings).toFixed(2);
                app.pastAcceptedInvitations[i].show_up_fee = parseFloat(app.pastAcceptedInvitations[i].show_up_fee).toFixed(2);
            }
        },

        viewConsentForm:function viewConsentForm(id, type, view_mode){
            window.open("/subjectConsent/" + id + "/" + type + "/" + view_mode +"/", '_self');
        },

        formatDate: function formatDate(value,value2,enable_time,length){
                if (value) {
                    return value;

                    //console.log(value);       
                    // rValue =   moment(String(value)).local().format('dddd');
                    // rValue +=   "<br>";
                    // rValue +=   moment(String(value)).local().format('M/D/YYYY');   
                    // rValue += "<br>";

                    // if(enable_time)
                    // {
                    //     rValue += moment(String(value)).local().format('h:mma'); 
                    //     if(value2 != null)
                    //     {
                    //         rValue += "-" + moment(String(value2)).local().format('h:mma'); 
                    //     }  
                    // }
                    // else
                    // {
                    //     rValue += "Anytime";
                        
                    //     if(length != null)
                    //     {
                    //         rValue += ", " + length + " min";
                    //     }
                    // }    
                    // return rValue;
                }
                else{
                    return "date format error";
                }
        },
  
    },


    mounted(){
             
        Vue.nextTick(() => {
            app.getCurrentInvitations();  
            app.subject_consent_form_modal = new bootstrap.Modal(document.getElementById('subject_consent_form_modal'), {keyboard: false});                     
            window.addEventListener('resize', app.handleResize);  
        }); 

           
    },
}).mount('#app');