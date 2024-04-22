axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],
      
    data(){return{
        sessionDayUsers:[],
        payGroup:"{{payGroup|safe}}",
        payoutTotal:"",
        experiment_session_day:null,
        consentForm:{{consent_form|safe}},
    }},

    methods:{
        //get the session day json info
        getSession:function(payGroup){           
            if(app)
            {                
                for(let i=0;i<app.sessionDayUsers.length;i++)
                {
                    if(app.sessionDayUsers[i].pixi_app)
                    {
                        // app.clearPixi(app.sessionDayUsers[i].pixi_app, 
                        //               "signature_canvas_id_" + app.sessionDayUsers[i].id );
                        
                        app.sessionDayUsers[i].pixi_app.stage.removeChildren();
                        app.sessionDayUsers[i].pixi_app.destroy(true,true);
                    }
                }

                app.sessionDayUsers =[];
            }

            axios.post('/experimentSessionPayouts/{{id}}/'+payGroup+'/', {
                action : "getSession" ,  
                payGroup : payGroup,                                                                                                                           
            })
            .then(function (response) {     
                app.sessionDayUsers = response.data.sessionDayUsers;   
                app.payGroup = payGroup;
                app.experiment_session_day = response.data.experiment_session_day;
                
                app.calcPayoutTotal();

                setTimeout(app.setupPixi, 500);
            })
            .catch(function (error) {
                console.log(error);                                   
            });                        
        },  

        //hide subject from list and payout total
        hideSubject:function(id, localIndex){
            u = app.sessionDayUsers.splice(localIndex,1);
           
            app.calcPayoutTotal();
        },

        //calc payout total of visible subjects
        calcPayoutTotal:function(){
            var s = 0;

            for(i=0;i<app.sessionDayUsers.length;i++)
            {
                u = app.sessionDayUsers[i];

                if(u.show)
                {
                    s += parseFloat(u.payout);                              
                }
            }

            app.payoutTotal = s.toFixed(2);
        },

        //format date to human readable
        formatDate: function(value){
            if (value) {        
                //console.log(value);                    
                return moment(String(value)).local().format('MM/DD/YYYY hh:mm a');
            }
            else{
                return "date format error";
            }
        },

        {%include "staff/experiment_session_payouts/pixi_setup.js"%}
    },

    mounted(){
            this.getSession("{{payGroup}}");                    
    },
}).mount('#app');