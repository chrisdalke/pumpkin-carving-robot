filename = 'calibration.csv';
m = csvread(filename);
theta = m(:,2);
rho = m(:,3);
z = m(:,1);

[x,y,z] = pol2cart(theta, rho, z);
scatter3(x,y,z,...
  'MarkerEdgeColor','r',...
  'MarkerFaceColor',[1 .6 0])

title('Pumpkin Scan')