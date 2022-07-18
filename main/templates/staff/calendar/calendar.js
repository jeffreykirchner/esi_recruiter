axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{
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
    },

    methods:{
        //get current, last or next month

        getMonth:function(){

            if( typeof app == 'undefined')
            {
                load_url_month = true;
            }
            else
            {
                load_url_month = app.$data.load_url_month;
                app.$data.working = true;
            }
               
            axios.post('{{request.path}}', {
                    action :"getMonth" , 
                    load_url_month : load_url_month,                            
                })
                .then(function (response) {     
                    app.updateMonth(response);  

                    app.$data.locations = response.data.locations;     
                    app.$data.todayDay = response.data.todayDay;
                    app.$data.todayMonth = response.data.todayMonth; 
                    app.$data.todayYear = response.data.todayYear;           
                    
                    app.$data.working = false;
                    app.$data.load_url_month = false;

                    setTimeout(app.scollToToday, 250);
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },

        //get new month's data
        changeMonth:function(direction){
            app.$data.working = true;

            // if(direction == "next")
            // {
            //     app.$data.forwardButtonText='<i class="fas fa-spinner fa-spin"></i>';
            // }
            // else
            // {
            //     app.$data.backButtonText='<i class="fas fa-spinner fa-spin"></i>';
            // }

            axios.post('/calendar/', {
                    action :"changeMonth" , 
                    direction: direction,
                    currentMonth: app.$data.currentMonth,
                    currentYear: app.$data.currentYear,
                })
                .then(function (response) {     
                    app.updateMonth(response);
                    
                    app.$data.working = false;

                    // app.$data.backButtonText="<<";
                    // app.$data.forwardButtonText=">>";
                })
                .catch(function (error) {
                    console.log(error);                            
                });                        
            },
        
        //show day modal
        showDayModal:function(weekIndex, dayIndex, dayString){
            currentSessions = app.$data.calendar[weekIndex][dayIndex].sessions;

            displayDayLocations=[];

            app.$data.displayDay.no_experiments = true;

            for(i=0;i<app.$data.locations.length;i++)
            {
                l = app.$data.locations[i];
                sessionList = [];

                for(j=0;j<currentSessions.length;j++)
                {
                    if(currentSessions[j].location.id == l.id)
                    {
                        sessionList.push(currentSessions[j]);
                        app.$data.displayDay.no_experiments = false;
                    }
                }

                displayDayLocations.push({"location":l.name,
                                            "sessions":sessionList,
                                        })
            }

            app.$data.displayDay.sessionLocations = displayDayLocations;
            app.$data.displayDay.dayString = dayString;

            $('#calendarDayModal').modal('toggle');

        },

        //jump to new month
        jump_to_new_month:function()
        {
            app.$data.working = true;

            axios.post('/calendar/', {
                action :"jump_to_month" , 
                new_month: app.$data.jump_to_month,
            })
            .then(function (response) {     
                app.updateMonth(response);

               app.$data.working = false;
            })
            .catch(function (error) {
                console.log(error);                            
            }); 
        },

        //update the current month's da
        updateMonth:function(response){
            app.$data.currentMonth = response.data.currentMonth;
            app.$data.currentYear = response.data.currentYear;       
            app.$data.calendar = response.data.calendar;          
            app.$data.currentMonthString = response.data.currentMonthString; 
            app.$data.jump_to_month = response.data.jump_to_month;

            history.replaceState({}, null, '/calendar/' + app.$data.currentMonth +'/' + app.$data.currentYear + '/');

            
        },

        //scroll to today's cell
        scollToToday(){
            v = "id_" + app.$data.todayDay + "_" + app.$data.todayMonth + "_" + app.$data.todayYear;
            var elmnt = document.getElementById(v);

            if(elmnt) elmnt.scrollIntoView(); 
        },
    },            

    mounted: function(){
        this.getMonth();                          
    },
});