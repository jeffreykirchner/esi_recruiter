axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = Vue.createApp({

    delimiters: ['[[', ']]'],       

    data(){return{
        calendar:[],
        todayDay:"",
        todayMonth:"",
        todayYear:"",
        currentMonth:"",
        currentYear:"",
        currentMonthString:"",
        locations:[],
        displayDay:{dayString:"",
                    no_experiments:true,
                    sessionLocations:[],
                    },
        // forwardButtonText:">>",
        // backButtonText:"<<",
        jump_to_month : "",
        working : true,
        load_url_month : true,
    }},

    methods:{
        //get current, last or next month

        getMonth:function(){

            if( typeof app == 'undefined')
            {
                load_url_month = true;
            }
            else
            {
                load_url_month = app.load_url_month;
                app.working = true;
            }
               
            axios.post('{{request.path}}', {
                    action :"getMonth" , 
                    load_url_month : load_url_month,                            
                })
                .then(function (response) {     
                    app.updateMonth(response);  

                    app.locations = response.data.locations;     
                    app.todayDay = response.data.todayDay;
                    app.todayMonth = response.data.todayMonth; 
                    app.todayYear = response.data.todayYear;           
                    
                    app.working = false;
                    app.load_url_month = false;

                    setTimeout(app.scollToToday, 250);
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },

        //get new month's data
        changeMonth:function(direction){
            app.working = true;

            // if(direction == "next")
            // {
            //     app.forwardButtonText='<i class="fas fa-spinner fa-spin"></i>';
            // }
            // else
            // {
            //     app.backButtonText='<i class="fas fa-spinner fa-spin"></i>';
            // }

            axios.post('/calendar/', {
                    action :"changeMonth" , 
                    direction: direction,
                    currentMonth: app.currentMonth,
                    currentYear: app.currentYear,
                })
                .then(function (response) {     
                    app.updateMonth(response);
                    
                    app.working = false;

                    // app.backButtonText="<<";
                    // app.forwardButtonText=">>";
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },
        
        //show day modal
        showDayModal:function(weekIndex, dayIndex, dayString){
            currentSessions = app.calendar[weekIndex][dayIndex].sessions;

            displayDayLocations=[];

            app.displayDay.no_experiments = true;

            for(i=0;i<app.locations.length;i++)
            {
                l = app.locations[i];
                sessionList = [];

                for(j=0;j<currentSessions.length;j++)
                {
                    if(currentSessions[j].location.id == l.id)
                    {
                        sessionList.push(currentSessions[j]);
                        app.displayDay.no_experiments = false;
                    }
                }

                displayDayLocations.push({"location":l.name,
                                            "sessions":sessionList,
                                        })
            }

            app.displayDay.sessionLocations = displayDayLocations;
            app.displayDay.dayString = dayString;

            $('#calendarDayModal').modal('toggle');

        },

        //jump to new month
        jump_to_new_month:function()
        {
            app.working = true;

            axios.post('/calendar/', {
                action :"jump_to_month" , 
                new_month: app.jump_to_month,
            })
            .then(function (response) {     
                app.updateMonth(response);

               app.working = false;
            })
            .catch(function (error) {
                console.log(error);                            
            }); 
        },

        //update the current month's da
        updateMonth:function(response){
            app.currentMonth = response.data.currentMonth;
            app.currentYear = response.data.currentYear;       
            app.calendar = response.data.calendar;          
            app.currentMonthString = response.data.currentMonthString; 
            app.jump_to_month = response.data.jump_to_month;

            history.replaceState({}, null, '/calendar/' + app.currentMonth +'/' + app.currentYear + '/');

            
        },

        //scroll to today's cell
        scollToToday(){
            v = "id_" + app.todayDay + "_" + app.todayMonth + "_" + app.todayYear;
            var elmnt = document.getElementById(v);

            if(elmnt) elmnt.scrollIntoView(); 
        },
    },            

    mounted(){
        this.getMonth();                          
    },
}).mount('#app');