axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

var app = new Vue({

    delimiters: ['[[', ']]'],
    el: '#root',        
    data:{
        sessionDay:{
            confirmedCount:"",
            attendingCount:"",
            bumpCount:"",
            requiredCount:"",
            experiment_session_days_user:[],    
            defaultShowUpFee : "",      
            complete:true,                
            canceled:false,
            reopenAllowed:false,      
            paypalAPI:true,     
        },
        bumpButtonText : '<i class="fa fa-arrow-left" aria-hidden="true"></i> Bump',
        noShowButtonText : '<i class="fa fa-arrow-left" aria-hidden="true"></i> No Show',
        attendButtonText : '<i class="fa fa-arrow-left" aria-hidden="true"></i> Attend',
        waitButtonText : '<i class="fas fa-spinner fa-spin"></i>',
        dateText:'<i class="fa fa-spinner fa-spin" aria-hidden="true"></i>',
        saveButtonText: 'Save Payouts <i class="far fa-save" aria-hidden="true"></i>',
        fillShowUpFeeButtonText : "Fill Bonus: $",
        completeSessionButtonText : 'Complete Session <i class="fas fa-check"></i>',
        openSessionButtonText : 'Re-Open Session <i class="fas fa-book-open"></i>',
        bumpAllButtonText : 'Bump All <i class="fas fa-user-slash"></i>',
        autoBumpButtonText : 'Auto Bump <i class="fa fa-random" aria-hidden="true"></i>',
        printPayoutsButtonText : 'Print Attendees <i class="fas fa-print"></i>',
        printBumpsButtonText : 'Print Bumps <i class="fas fa-print"></i>',
        paypalExportButtonText : 'Paypal Export <i class="fab fa-paypal"></i>',
        paypalDirectButtonText : 'Paypal Direct <i class="fab fa-paypal"></i>',
        earningsExportButtonText : 'Attended Export <i class="fas fa-download"></i>',
        roundUpButtonText : 'Round Earnings <i class="fas fa-circle-notch"></i>',
        fillEarningsWithFixedButtonText : 'Fill',
        updatePayoutsRequired : false,             //need to send payouts update
        updatingPayoutsInProgress : false,         //currently sending a payouts update
        payoutTotal:"",                            //total paid to subjects
        fillEarningsWithValue:"",                   //amount to fill all earnings with
        isAdmin:{%if user.is_superuser%}true{%else%}false{%endif%},  
        stripeReaderSpinner : "",
        stripeReaderValue : "",
        stripeReaderStatus : "",
        autoAddUsers :false,                         //automatically add users if they are not checked in
        ignoreConstraints:false,                    //ignore recruitment constraints and add user
        upload_file : null,
        upload_file_name:'Choose File',
        uploadEarningsButtonText:'Upload <i class="fas fa-upload"></i>',
        uploadEarningsMessage:'',
        noticeHeader : "PayPal Direct Payments",
        noticeBody : "",
        auto_add_users_on_upload : false,  
    },

    methods:{
        //get the session day json info
        getSession:function(){
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"getSession" ,                                                                                                                             
                })
                .then(function (response) {     
                    app.$data.sessionDay= response.data.sessionDay; 
                    app.calcPayoutTotal();      

                    app.$data.dateText = app.$data.sessionDay.date;      
                    app.$data.dateText += " | " + app.$data.sessionDay.length + " Minutes";
                    app.$data.dateText += " | " + app.$data.sessionDay.location.name;    
                    
                    app.$data.fillShowUpFeeButtonText += app.$data.sessionDay.defaultShowUpFee;

                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },

        //stripe reader checkin
        stripeReaderCheckin:function(){
            window.setTimeout(this.stripeReaderCheckin, 250);
            
            if(app.$data.stripeReaderValue == "") return;
            if(app.$data.stripeReaderSpinner != "") return;
            if(!app.$data.stripeReaderValue.includes("=")) return;

            app.$data.stripeReaderSpinner = '<i class="fas fa-spinner fa-spin"></i>';
            app.$data.stripeReaderStatus="";

            axios.post('/experimentSessionRun/{{id}}/', {
                        action :"stripeReaderCheckin" ,
                        value:app.$data.stripeReaderValue,    
                        autoAddUsers:app.$data.autoAddUsers,   
                        ignoreConstraints:app.$data.ignoreConstraints,                                                                                                                        
                    })
                    .then(function (response) {                                
                    app.$data.sessionDay = response.data.sessionDay;   
                    app.$data.stripeReaderSpinner = "";   
                    app.$data.stripeReaderValue = "";    
                    app.$data.stripeReaderStatus = response.data.status.message;

                    ids =  response.data.status.info;
                    for(i=0;i<ids.length;i++)
                    {
                        app.$data.stripeReaderStatus += " <a href='/userInfo/" + ids[i] + "/' target='_blank' >view</a>";
                    }

                    })
                    .catch(function (error) {
                        console.log(error);                                   
                    });
        },

        //export a csv file for paypal mass payment
        payPalExport:function(){
            if(app.$data.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }
            
            app.$data.paypalExportButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            
            axios.post('/experimentSessionRun/{{id}}/', {
                        action :"payPalExport" ,                                                                                                                                                      
                    })
                    .then(function (response) {      
                    
                    // let csvContent = "data:text/csv;charset=utf-8,";
                    // csvContent = response

                    console.log(response)

                    var downloadLink = document.createElement("a");
                    var blob = new Blob(["\ufeff", response.data]);
                    var url = URL.createObjectURL(blob);
                    downloadLink.href = url;
                    downloadLink.download = "PayPal_Mass_Pay_" + app.$data.sessionDay.id + ".csv";

                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);

                    app.$data.paypalExportButtonText = 'Paypal Export <i class="fab fa-paypal"></i>';                  
                    })
                    .catch(function (error) {
                        console.log(error);                                   
                    });
        },

        //export an earnings csv file 
        earningsExport:function(){
            if(app.$data.saveButtonText.indexOf("*") >= 0)
            {   
                confirm("Save payouts before continuing.") ;                    
                return;                        
            }
            
            app.$data.earningsExportButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            
            axios.post('/experimentSessionRun/{{id}}/', {
                        action :"getEarningsExport" ,                                                                                                                                                      
                    })
                    .then(function (response) {      
                    
                    // let csvContent = "data:text/csv;charset=utf-8,";
                    // csvContent = response

                    console.log(response)

                    var downloadLink = document.createElement("a");
                    var blob = new Blob(["\ufeff", response.data]);
                    var url = URL.createObjectURL(blob);
                    downloadLink.href = url;
                    downloadLink.download = "Attending_Export_" + app.$data.sessionDay.id + ".csv";

                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);

                    app.$data.earningsExportButtonText = 'Attended Export <i class="fas fa-download"></i>';                  
                    })
                    .catch(function (error) {
                        console.log(error);                                   
                    });
        },

        //randomly bump excess subjects
        autobump:function(){
            app.$data.autoBumpButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            
            // esdu.buttonText = '<i class="fas fa-spinner fa-spin"></i>'
                axios.post('/experimentSessionRun/{{id}}/', {
                        action :"autoBump" ,   
                                                                                                                                            
                    })
                    .then(function (response) {                                
                    app.$data.sessionDay = response.data.sessionDay;    

                    app.$data.autoBumpButtonText = 'Auto Bump <i class="fa fa-random" aria-hidden="true"></i>';                    
                    })
                    .catch(function (error) {
                        console.log(error);                                   
                    });                        
        },
        
        //set subject to attended
        attendSubject:function(esduID,id){
            app.$data.sessionDay.experiment_session_days_user[id].waiting = true;
            
            // esdu.buttonText = '<i class="fas fa-spinner fa-spin"></i>'
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"attendSubject" ,   
                    id:esduID, 
                    localId:id,                                                                                                                         
                })
                .then(function (response) {                                
                    app.$data.sessionDay = response.data.sessionDay;     
                    app.$data.stripeReaderStatus= response.data.status;                   
                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },

        //set subject to bumped
        bumpSubject:function(esduID,id){
            app.$data.sessionDay.experiment_session_days_user[id].waiting = true;

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"bumpSubject" ,   
                    id:esduID,                                                                                                            
                })
                .then(function (response) {     
                    app.$data.sessionDay = response.data.sessionDay;  
                    app.$data.stripeReaderStatus= response.data.statusMessage;                                                               
                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },
        
        //set subject to no show
        noShowSubject:function(esduID,id){
            app.$data.sessionDay.experiment_session_days_user[id].waiting = true;
            
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"noShowSubject" , 
                    id:esduID,                                                                                                                            
                })
                .then(function (response) {     
                    app.$data.sessionDay = response.data.sessionDay;    
                    app.$data.stripeReaderStatus = "";                                                                  
                })
                .catch(function (error) {
                    console.log(error);                                   
                });                        
            },
        
        //save the current payouts
        savePayouts:function(){
            app.$data.saveButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"savePayouts" ,  
                    payoutList : app.getPayoutlist(),                                                                                                                           
                })
                .then(function (response) {     
                    app.$data.sessionDay= response.data.sessionDay;      
                    app.$data.saveButtonText = 'Save Payouts <i class="far fa-save" aria-hidden="true"></i>';
                    app.calcPayoutTotal();
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //finsh session, prevents further editing
        completeSession:function(){

            if(app.$data.saveButtonText.indexOf("*") >= 0)
            {   
                confirm("Save payouts before continuing.") ;                    
                return;                        
            }

            app.$data.completeSessionButtonText = '<i class="fas fa-spinner fa-spin"></i>';
            app.$data.openSessionButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"completeSession" ,                                                                                                                             
                })
                .then(function (response) {     
                    app.$data.sessionDay = response.data.sessionDay;     
                    
                    app.$data.completeSessionButtonText = 'Complete Session <i class="fas fa-check"></i>';
                    app.$data.openSessionButtonText = 'Re-Open Session <i class="fas fa-book-open"></i>';
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //calc payout total of visible subjects
        calcPayoutTotal:function(){
            var s = 0;

            for(i=0;i<app.$data.sessionDay.experiment_session_days_user.length;i++)
            {
                u = app.$data.sessionDay.experiment_session_days_user[i];

                if(u.show)
                {
                    s += parseFloat(u.payout);                              
                }
            }

            app.$data.payoutTotal = s.toFixed(2);
        },

        //fill subjects with default show up fee from experiments model
        fillWithDefaultShowUpFee:function(){
            app.$data.fillShowUpFeeButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"fillDefaultShowUpFee" ,                                                                                                                             
                })
                .then(function (response) {     
                    app.$data.sessionDay = response.data.sessionDay;   
                    app.$data.fillShowUpFeeButtonText = "Fill Bonus: $" + app.$data.sessionDay.defaultShowUpFee; 
                    app.calcPayoutTotal();                     
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //fill subjects with default show up fee from experiments model
        fillEarningsWithFixed:function(){

            if(app.$data.fillEarningsWithValue=="") return;

            app.$data.fillEarningsWithFixedButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"fillEarningsWithFixed" ,
                    amount: app.$data.fillEarningsWithValue,                                                                                                                             
                })
                .then(function (response) {     
                    app.$data.sessionDay = response.data.sessionDay;    
                    app.$data.fillEarningsWithFixedButtonText = "Fill";
                    app.$data.fillEarningsWithValue="";    
                    app.calcPayoutTotal();                          
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //run when key pressed in payouts box
        payoutsKeyUp:function(userId,localId){
            app.$data.saveButtonText = 'Save Payouts <i class="far fa-save" aria-hidden="true"></i> *';
        },

        //when user changes the payouts, auto save
        payoutsChange:function(userId,localId){
            app.$data.saveButtonText = 'Save Payouts <i class="far fa-save" aria-hidden="true"></i> *';
            
            if(app.$data.updatingPayoutsInProgress)
            {
                app.$data.updatePayoutsRequired = true;
                return;
            }
            else
            {
                app.$data.updatePayoutsRequired = false;
                app.$data.updatingPayoutsInProgress = true;
            }                  
            
            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"backgroundSave", 
                    payoutList : app.getPayoutlist(),                                                                                                                    
                })
                .then(function (response) {     
                    status = response.data.status;    

                    if(status == "success")
                    {
                        app.$data.updatingPayoutsInProgress = false;
                    }
                    else
                    {

                    }

                    if(app.$data.updatePayoutsRequired){
                        app.payoutsChange(userId,localId); 
                    }
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },   

        //return a list of the payouts entered by the user
        getPayoutlist:function(){
            payoutList=[];

            for(var i=0;i<app.$data.sessionDay.experiment_session_days_user.length;i++)
            {
                tempU = app.$data.sessionDay.experiment_session_days_user[i];
                tempV = {"id":tempU.id,
                        "earnings":tempU.earnings,
                        "showUpFee":tempU.show_up_fee,
                        }
                payoutList.push(tempV);
            }

            return payoutList;
        },             

        //bump all present users
        bumpAll:function(){
            app.$data.bumpAllButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"bumpAll"                                                                                                                            
                })
                .then(function (response) {     
                    app.$data.sessionDay= response.data.sessionDay;      
                    app.$data.bumpAllButtonText = 'Bump All <i class="fas fa-user-slash"></i>';
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //print payouts
        printPayouts:function(){
            if(app.$data.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }

            window.open('/experimentSessionPayouts/' + app.$data.sessionDay.id +'/payouts/', '_blank');
        },

        //print bumps
        printBumps:function(){
            if(app.$data.saveButtonText.indexOf("*") >= 0)
            {  
                alert("Save payouts before continuing.") ;                      
                return;                        
            }

            window.open('/experimentSessionPayouts/' + app.$data.sessionDay.id +'/bumps/', '_blank');
        },

        //upload earings file csv
        uploadEarnings:function(){

            if(app.$data.upload_file == null)
                return;

            app.$data.uploadEarningsMessage = "";
            app.$data.uploadEarningsButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            let formData = new FormData();
            formData.append('file', app.$data.upload_file);
            formData.append('auto_add', app.$data.auto_add_users_on_upload);

            axios.post('/experimentSessionRun/{{id}}/', formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                            }
                        } 
                    )
                    .then(function (response) {     

                        app.$data.uploadEarningsMessage = response.data.message;

                        app.$data.uploadEarningsButtonText= 'Upload <i class="fas fa-upload"></i>';
                        app.$data.sessionDay = response.data.sessionDay;   
                        app.calcPayoutTotal();                                                                             
                    })
                    .catch(function (error) {
                        console.log(error);
                        app.$data.searching=false;
                    });                        
                },

        //store the location of the file to be uploaded
        handleFileUpload:function(){
            app.$data.upload_file = this.$refs.file.files[0];
            //$('parameterFileUpload').val("");
            app.$data.upload_file_name = app.$data.upload_file.name;

        },

        //fire when show upload earnings
        showUploadEarnings:function(){
            app.$data.uploadEarningsMessage = "";
            $('#uploadEarningsModal').modal('show');
        },

        hideUploadEarnings:function(){
        },
        
        //fill subjects with default show up fee from experiments model
        roundEarningsUp:function(){

            if(app.$data.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }

            app.$data.roundUpButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"roundEarningsUp",                                                                                                                           
                })
                .then(function (response) {     
                    app.$data.sessionDay = response.data.sessionDay;    
                    app.$data.roundUpButtonText = 'Round Earnings <i class="fas fa-circle-notch"></i>';   
                    app.calcPayoutTotal();                       
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
        },

        //pay subjects with PayPal API
        payPalAPI:function(){
            var r = confirm("Pay subjects directly with PayPal's API?");

            if (r == false)
            {
                return;
            }

            if(app.$data.saveButtonText.indexOf("*") >= 0)
            {   
                alert("Save payouts before continuing.") ;                    
                return;                        
            }

            app.$data.paypalDirectButtonText = '<i class="fas fa-spinner fa-spin"></i>';

            axios.post('/experimentSessionRun/{{id}}/', {
                    action :"payPalAPI",                                                                                                                           
                })
                .then(function (response) {     
                    
                    app.$data.sessionDay = response.data.sessionDay;
                    app.$data.paypalDirectButtonText = 'Paypal Direct <i class="fab fa-paypal"></i>';           
                    
                    if( response.data.error_message != "")
                    {
                        app.$data.noticeBody = response.data.error_message;
                    }
                    else
                    {
                        app.$data.noticeBody = response.data.result;
                    }

                    $('#noticeModal').modal('toggle');
                })
                .catch(function (error) {
                    console.log(error);                                   
                });
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
    },

    mounted: function(){
            this.getSession();       
            window.setTimeout(this.stripeReaderCheckin, 250);      
            $('#hideUploadEarnings').on("hidden.bs.modal", this.hideEditSubject);       
    },
});