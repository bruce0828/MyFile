% plot scatter figure with daily trace in Matlab

H = figure;
stop_id = find(stop == 1);
trip_id = find(stop == 0);
scatter3(lon(stop_id), lat(stop_id), num(stop_id), 'r', 'SizeData',5);
hold on
scatter3(lon(trip_id), lat(trip_id), num(trip_id), 'b', 'SizeData', 1);
%set(gca,'ZTick',[0.0 10800 21600 32400 43200 54000 64800 75600 86399]);
%set(gca,'zticklabel',({'0:00','3:00','6:00','9:00','12:00','15:00','18:00','21:00','24:00'}));
set(gca,'ZTick',[0 21600 43200 64800 86399]);
set(gca,'zticklabel',({'00:00','06:00','12:00','18:00','24:00'}));
zlim([0,86400]);
%xlabel('Longitude');
%ylabel('Latitude');
%zlabel('Timestamp');
%set(get(gca,'XLabel'),'Fontsize',20);
%set(get(gca,'YLabel'),'Fontsize',20);
%set(get(gca,'ZLabel'),'Fontsize',20);
%set(gca,'xticklabel',[],'yticklabel',[],'zticklabel',[])
hold off
