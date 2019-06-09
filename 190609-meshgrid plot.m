% 职住识别参数画图

% 南京-----------------------------------------------------
x = 10:22;
y = 10:22;
[X,Y] = meshgrid(x);
surf(X,Y,ressnj);
colormap(flipud(jet));   % jet色阶倒转
colorbar([0.92 0.25 0.01 0.5]);
caxis([0.5 1]);

% X axis
xlabel('工作地停留天数','FontSize',14);
xlh = get(gca,'XLabel');
gxl = get(xlh);
xlp = get(xlh,'Position');
set(xlh,'Rotation',15,'Position',ylp+[7 -6 0]);
set(gca,'XTick',10:2:22,'fontsize',12);

% Y axis
ylabel('居住地停留天数','FontSize',14);
ylh = get(gca,'YLabel');
gyl = get(ylh);
ylp = get(ylh,'Position');
set(ylh,'Rotation',-25,'Position',ylp+[1 -2 0]);
set(gca,'YTick',10:2:22,'fontsize',12);

% Z axis
zlabel('MAPE','FontSize',14);



% 上海-----------------------------------------------------
x = 10:22;
y = 10:22;
[X,Y] = meshgrid(x);
surf(X,Y,resssh);
colormap(flipud(jet));   % jet色阶倒转
colorbar([0.92 0.25 0.01 0.5]);
caxis([1.8, 3.5]);

% X axis
xlabel('工作地停留天数','FontSize',14);
xlh = get(gca,'XLabel');
gxl = get(xlh);
xlp = get(xlh,'Position');
set(xlh,'Rotation',15,'Position',ylp+[7 -6 0]);
set(gca,'XTick',10:2:22,'fontsize',12);

% Y axis
ylabel('居住地停留天数','FontSize',14);
ylh = get(gca,'YLabel');
gyl = get(ylh);
ylp = get(ylh,'Position');
set(ylh,'Rotation',-25,'Position',ylp+[1 -2 0]);
set(gca,'YTick',10:2:22,'fontsize',12);

% Z axis
zlabel('MAPE','FontSize',14);
